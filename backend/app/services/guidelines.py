"""Hardcoded clinical guideline snippets for referral generation (B3).

No vector RAG — `rag.py` stays a stub. These strings are injected into the
LLM prompt and reused verbatim by the deterministic template fallback so
both paths cite the same clinical basis.
"""

GUIDELINE_SNIPPETS: list[str] = [
    "FIB-4 <1.3 indicates a low probability of advanced fibrosis; 1.3-2.67 is an "
    "indeterminate 'grey zone' requiring further workup; >2.67 indicates a high "
    "probability of advanced fibrosis (AASLD/EASL non-invasive fibrosis staging).",
    "In patients over 65, the FIB-4 low-risk cutoff should be raised (commonly to 2.0) "
    "because age alone inflates the score, reducing specificity in older adults.",
    "APRI >1.0 suggests significant hepatic fibrosis and supports specialist referral "
    "(WHO guidance for hepatitis C management in resource-limited settings).",
    "A positive anti-HCV antibody result requires reflex HCV RNA testing to confirm "
    "active/chronic infection before any treatment decision (CDC/AASLD-IDSA HCV testing guidance).",
    "Patients with an indeterminate or high-risk fibrosis score and no follow-up testing "
    "within 6 months should be flagged for repeat labs or transient elastography (FibroScan).",
]


def get_guideline_snippets() -> list[str]:
    return GUIDELINE_SNIPPETS
