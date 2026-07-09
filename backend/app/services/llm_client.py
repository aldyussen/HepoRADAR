"""Gemini LLM client for referral generation (B3).

Primary path only — the mandatory template fallback lives in
`services/referral.py`. Any failure here (missing key, network error, 429
rate limit, empty/malformed response) must raise so the caller falls back;
this module never returns a partial or best-effort referral.
"""

import logging

from app.config import settings

logger = logging.getLogger(__name__)

_REFERRAL_PROMPT_TEMPLATE = """You are a clinical referral assistant. Produce a referral \
letter with EXACTLY these four section headings, in this order, and no others:

Patient Summary:
Risk Scores:
Key Drivers:
Recommendation:

Do not add a preamble, closing remarks, or any section not listed above. Be concise \
and clinical.

Patient summary:
{patient_summary}

Risk scores:
{scores}

Key drivers (most important first):
{top_factors}

Relevant clinical guideline snippets to ground the recommendation:
{guideline_snippets}
"""


def generate_referral(
    patient_summary: str,
    scores: dict,
    top_factors: list[dict],
    guideline_snippets: list[str],
) -> str:
    """Call Gemini to draft a referral letter. Raises on ANY failure."""
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured")

    from google import genai  # lazy import: SDK is only needed on the LLM path

    scores_text = "\n".join(f"- {k}: {v}" for k, v in scores.items()) or "- none available"
    factors_text = (
        "\n".join(
            f"- {f.get('feature')}: value={f.get('value')} ({f.get('direction')})"
            for f in top_factors
        )
        or "- none available"
    )
    guidelines_text = "\n".join(f"- {g}" for g in guideline_snippets)

    prompt = _REFERRAL_PROMPT_TEMPLATE.format(
        patient_summary=patient_summary,
        scores=scores_text,
        top_factors=factors_text,
        guideline_snippets=guidelines_text,
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model=settings.gemini_model, contents=prompt)

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise RuntimeError("Gemini returned an empty response")

    return text.strip()
