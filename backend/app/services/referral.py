"""Referral orchestrator (B3): LLM primary, deterministic template fallback.

Golden rule: the referral button must ALWAYS produce a valid referral. Any
failure on the LLM path (network error, rate limit, missing key, malformed
response) falls through to a template built from the same fields — this
function never raises to its caller.
"""

import logging

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.referral import Referral
from app.services import llm_client
from app.services.guidelines import get_guideline_snippets

logger = logging.getLogger(__name__)

_SEX_LABELS = {1: "male", 0: "female"}


def _patient_summary(patient: Patient) -> str:
    age = patient.age if patient.age is not None else "unknown age"
    sex = _SEX_LABELS.get(patient.sex, "unknown sex")
    return f"Patient MRN {patient.mrn}, {age}, {sex}."


def _render_template(patient: Patient, scores: dict, factors: list[dict], guideline_snippets: list[str]) -> str:
    scores_lines = "\n".join(f"- {k}: {v}" for k, v in scores.items()) or "- no scores available"

    if factors:
        factors_lines = "\n".join(
            f"- {f.get('feature')}: value={f.get('value')} ({f.get('direction')})" for f in factors
        )
    else:
        factors_lines = "- No individual risk drivers available."

    zone = scores.get("zone")
    if zone == "high":
        recommendation = (
            "High-risk fibrosis score. Recommend referral to hepatology for further evaluation "
            "(e.g. transient elastography or biopsy) and HCV RNA reflex testing if anti-HCV positive."
        )
    elif zone == "grey":
        recommendation = (
            "Indeterminate (grey-zone) fibrosis score. Recommend repeat liver panel in 3-6 months "
            "or non-invasive fibrosis staging (e.g. FibroScan) to clarify risk."
        )
    elif zone == "low":
        recommendation = "Low probability of advanced fibrosis on current labs. Recommend routine monitoring."
    else:
        recommendation = "Insufficient lab data to compute a fibrosis risk score. Recommend obtaining a complete liver panel (AST, ALT, platelets)."

    guidelines_lines = "\n".join(f"- {g}" for g in guideline_snippets)

    return (
        "Patient Summary:\n"
        f"{_patient_summary(patient)}\n\n"
        "Risk Scores:\n"
        f"{scores_lines}\n\n"
        "Key Drivers:\n"
        f"{factors_lines}\n\n"
        "Recommendation:\n"
        f"{recommendation}\n\n"
        "Guideline basis:\n"
        f"{guidelines_lines}"
    )


def build_referral(db: Session, patient: Patient, scores: dict, factors: list[dict]) -> Referral:
    """Generate and persist a referral for `patient`. Never raises."""
    guideline_snippets = get_guideline_snippets()
    summary = _patient_summary(patient)

    try:
        content = llm_client.generate_referral(summary, scores, factors, guideline_snippets)
        source, status = "llm", "draft"
    except Exception:
        logger.warning(
            "LLM referral generation failed for patient %s — falling back to template.",
            patient.id,
            exc_info=True,
        )
        content = _render_template(patient, scores, factors, guideline_snippets)
        source, status = "template", "template_fallback"

    referral = Referral(patient_id=patient.id, status=status, source=source, content=content)
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral
