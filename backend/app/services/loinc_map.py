"""Raw lab code/name -> canonical analyte mapping. Plain data, no logic.

Extend ANALYTES with real org codes as they're seen in ingested files.
"""

ANALYTES: dict[str, dict] = {
    "AST": {
        "loinc": "1920-8",
        "unit": "U/L",
        "range": (0, 5000),
        "aliases": [
            "ast", "sgot", "ast(u/l)", "astul", "aspartate aminotransferase",
            "аст",
        ],
    },
    "ALT": {
        "loinc": "1742-6",
        "unit": "U/L",
        "range": (0, 5000),
        "aliases": [
            "alt", "sgpt", "altgpt", "alanine aminotransferase",
            "алт",
        ],
    },
    "PLT": {
        "loinc": "777-3",
        "unit": "10^9/L",
        "range": (10, 1000),
        "aliases": [
            "plt", "platelets", "platelet count", "platelet",
            "тромбоциты",
        ],
    },
    "BILIRUBIN": {
        "loinc": "1975-2",
        "unit": "mg/dL",
        "range": (0, 50),
        "aliases": ["bilirubin", "total bilirubin", "bili", "tbil"],
    },
    "ALBUMIN": {
        "loinc": "1751-7",
        "unit": "g/dL",
        "range": (0, 10),
        "aliases": ["albumin", "alb"],
    },
    "ANTI_HCV": {
        "loinc": "13955-0",
        "unit": "S/CO",
        "range": (0, 100),
        "aliases": ["anti-hcv", "hcv antibody", "hcv_ab", "hcv ab", "антитела к гепатиту с"],
    },
    "HCV_RNA": {
        "loinc": "11011-4",
        "unit": "IU/mL",
        "range": (0, 100000000),
        "aliases": ["hcv rna", "hcv-rna", "hcv_rna", "рнк гепатита с"],
    },
}

# Demographic / identifier columns (not labs, but ingested from the same CSV)
DEMOGRAPHIC_ALIASES: dict[str, list[str]] = {
    "patient_id": ["patient_id", "mrn", "id", "patient", "patientid"],
    "age": ["age", "age_years", "ageyears", "возраст"],
    "sex": ["sex", "gender", "пол"],
    "date": ["date", "visit_date", "lab_date", "collection_date", "visitdate", "labdate"],
}

REQUIRED_ANALYTES = ("AST", "ALT", "PLT")


def normalize(name: str) -> str:
    """Lowercase, strip whitespace/punctuation for fuzzy comparison."""
    return "".join(ch for ch in name.strip().lower() if ch.isalnum())


def _best_match(column_name: str, alias_map: dict[str, list[str]]) -> str | None:
    normalized = normalize(column_name)
    if not normalized:
        return None
    for key, aliases in alias_map.items():
        if normalized in {normalize(a) for a in aliases}:
            return key
    return None


def match_analyte(column_name: str) -> str | None:
    """Return canonical analyte name (e.g. 'AST') for a raw column name, or None."""
    alias_map = {k: v["aliases"] for k, v in ANALYTES.items()}
    return _best_match(column_name, alias_map)


def match_demographic(column_name: str) -> str | None:
    """Return canonical demographic field name for a raw column name, or None."""
    return _best_match(column_name, DEMOGRAPHIC_ALIASES)
