"""Pure scoring functions. No DB, no I/O — fully unit-testable.

Every function guards against missing/invalid inputs and returns None rather
than raising, so callers can attach a quality flag instead of crashing.
"""

import math
from typing import Literal

import numpy as np
import pandas as pd

from app.config import settings

Zone = Literal["low", "grey", "high", "n/a"]

def fib4(age: float | None, ast: float | None, alt: float | None, plt: float | None) -> float | None:
    """FIB-4 = (age * AST) / (platelets * sqrt(ALT))."""
    if age is None or ast is None or alt is None or plt is None:
        return None
    if age < 0 or ast < 0 or alt <= 0 or plt <= 0:
        return None
    return (age * ast) / (plt * math.sqrt(alt))


def apri(ast: float | None, ast_uln: float | None, plt: float | None) -> float | None:
    """APRI = (AST / AST_ULN) / platelets * 100."""
    if ast is None or ast_uln is None or plt is None:
        return None
    if ast < 0 or ast_uln <= 0 or plt <= 0:
        return None
    return (ast / ast_uln) / plt * 100


def de_ritis(ast: float | None, alt: float | None) -> float | None:
    """De Ritis ratio = AST / ALT."""
    if ast is None or alt is None:
        return None
    if ast < 0 or alt <= 0:
        return None
    return ast / alt


def zone(fib4_val: float | None, age: float | None = None, ast: float | None = None, alt: float | None = None) -> Zone | None:
    """Map a FIB-4 value to a risk zone using thresholds from config.

    `age` is accepted for the >65 caveat noted in the plan but does not
    change the cutoffs here — standard adult cutoffs are used uniformly.
    """
    if age is not None:
        if age < 18:
            return "n/a"
        if age < 35:
            return "n/a"
            
    if (ast is not None and ast > 500) or (alt is not None and alt > 500):
        return "n/a"
    if fib4_val is None:
        return None
        
    low_cutoff = settings.fib4_low_max
    if age is not None and age >= 65:
        low_cutoff = 2.00
        
    if fib4_val < low_cutoff:
        return "low"
    if fib4_val > settings.fib4_high_min:
        return "high"
    return "grey"


def needs_age_caveat(age: float | None) -> bool:
    """True if FIB-4's standard cutoffs are less reliable for this patient's age."""
    return age is not None and age > settings.fib4_age_caveat_years


def fib4_to_risk(fib4_val: float | None) -> float | None:
    """Monotonic transform of FIB-4 onto [0, 1] — the mandatory ML fallback.

    Centered on the grey zone's midpoint so low/high FIB-4 push toward 0/1
    while grey-zone values stay near 0.5, matching the role a real model
    would play once trained.
    """
    if fib4_val is None:
        return None
    midpoint = (settings.fib4_low_max + settings.fib4_high_min) / 2
    return 1 / (1 + math.exp(-2.0 * (fib4_val - midpoint)))


# feature -> (direction that indicates risk, threshold)
_RULE_BASED_FACTOR_RULES = {
    "ast": ("high", 40.0),
    "alt": ("high", 40.0),
    "plt": ("low", 150.0),
    "albumin": ("low", 3.5),
    "bilirubin": ("high", 1.2),
}


def rule_based_factors(row: dict, max_factors: int = 3) -> list[dict]:
    """Fallback explanation when no SHAP explainer is available.

    Flags analytes past their normal-range threshold, ranked by how far past
    it they are. Not a real attribution — a readable substitute so `/explain`
    always returns something, e.g. "FIB-4 driven by low platelets + high AST".
    """
    factors = []
    for feature, (direction, threshold) in _RULE_BASED_FACTOR_RULES.items():
        value = row.get(feature)
        if value is None:
            continue
        if direction == "high" and value > threshold:
            magnitude = (value - threshold) / threshold
        elif direction == "low" and value < threshold:
            magnitude = (threshold - value) / threshold
        else:
            continue
        # For FIB-4, high ALT actually decreases the score (since it's in the denominator).
        # We reflect this mathematically in the rule-based explanation.
        dir_str = "decreases risk" if feature == "alt" and direction == "high" else "increases risk"
        
        factors.append(
            {"feature": feature, "value": value, "shap": round(magnitude, 3), "direction": dir_str}
        )

    factors.sort(key=lambda f: f["shap"], reverse=True)
    return factors[:max_factors]


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorized FIB-4/APRI/De Ritis/zone for the cohort scan endpoint.

    `df` must have numeric columns: age, ast, alt, plt. Rows with any missing
    or non-positive input yield NaN/None scores rather than raising, matching
    the scalar functions' guard behavior.
    """
    age, ast, alt, plt = df["age"], df["ast"], df["alt"], df["plt"]

    valid = age.notna() & ast.notna() & alt.notna() & plt.notna() & (alt > 0) & (plt > 0) & (age >= 0) & (ast >= 0)

    with np.errstate(divide="ignore", invalid="ignore"):
        fib4_vals = (age * ast) / (plt * np.sqrt(alt))
        apri_vals = (ast / settings.ast_uln) / plt * 100
        de_ritis_vals = ast / alt

    fib4_vals = fib4_vals.where(valid)
    apri_vals = apri_vals.where(valid)
    de_ritis_vals = de_ritis_vals.where(valid)

    zone_vals = pd.Series("grey", index=df.index)
    
    # Vectorized logic for geriatric thresholds
    mask_elderly = (age >= 65)
    mask_standard = (age < 65) | age.isna()
    
    zone_vals = np.where(mask_elderly & (fib4_vals < 2.0), "low", zone_vals)
    zone_vals = np.where(mask_standard & (fib4_vals < settings.fib4_low_max), "low", zone_vals)
    zone_vals = np.where(fib4_vals > settings.fib4_high_min, "high", zone_vals)
    
    zone_vals = pd.Series(zone_vals, index=df.index)
    zone_vals = zone_vals.where(fib4_vals.notna(), None)

    out = df.copy()
    out["fib4"] = fib4_vals
    out["apri"] = apri_vals
    out["de_ritis"] = de_ritis_vals
    out["zone"] = zone_vals
    out["quality_flags"] = ""
    
    # Age < 18 gate
    mask_pediatric = out["age"] < 18
    if mask_pediatric.any():
        out.loc[mask_pediatric, "zone"] = "n/a"
        out.loc[mask_pediatric, "quality_flags"] = "FIB-4 не применим в педиатрии (<18 лет)"
        
    # Age 18-34 gate
    mask_young = (out["age"] >= 18) & (out["age"] < 35)
    if mask_young.any():
        out.loc[mask_young, "zone"] = "n/a"
        out.loc[mask_young, "quality_flags"] = out.loc[mask_young, "quality_flags"].astype(str) + " | FIB-4 не валидирован <35 лет (Н/Д)"
        out.loc[mask_young, "quality_flags"] = out.loc[mask_young, "quality_flags"].str.lstrip(" | ")
        
    # Acute liver injury gate
    mask_acute = (out["ast"] > 500) | (out["alt"] > 500)
    if mask_acute.any():
        out.loc[mask_acute, "zone"] = "n/a"
        out.loc[mask_acute, "quality_flags"] = out.loc[mask_acute, "quality_flags"].astype(str) + " | FIB-4 не применим при АСТ/АЛТ > 500"
        
    return out
