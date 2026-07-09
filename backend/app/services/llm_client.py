"""Gemini LLM client for referral generation (B3).

Primary path only — the mandatory template fallback lives in
`services/referral.py`. Any failure here (missing key, network error, 429
rate limit, empty/malformed response) must raise so the caller falls back;
this module never returns a partial or best-effort referral.
"""

import logging

import json
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

def extract_labs_from_images(image_bytes_list: list[bytes], mime_types: list[str]) -> dict:
    """Extract lab values from images using Gemini Vision."""
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured")

    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field

    class ExtractedLabs(BaseModel):
        age: int | None = Field(description="Patient age if present")
        sex: int | None = Field(description="Patient sex (1 for male, 0 for female) if present")
        ast: float | None = Field(description="AST value if present")
        alt: float | None = Field(description="ALT value if present")
        plt: float | None = Field(description="Platelets (PLT) value if present")
        anti_hcv_pos: bool | None = Field(description="True if anti-HCV positive is indicated")
        hcv_rna_done: bool | None = Field(description="True if HCV RNA (PCR) test was done")
        status: str = Field(description="'ok' if at least some values are readable, 'unreadable' if not a lab report or completely blurry")
        hint: str | None = Field(description="Hint for the user if unreadable")

    client = genai.Client(api_key=settings.gemini_api_key)
    
    parts = ["Extract these values from the lab report image(s). Return JSON."]
    for img_bytes, mime_type in zip(image_bytes_list, mime_types):
        parts.append(
            types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedLabs,
        )
    )

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise RuntimeError("Gemini returned an empty response")

    return json.loads(text.strip())
