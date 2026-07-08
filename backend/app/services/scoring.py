"""Pure scoring functions. No DB, no I/O — fully unit-testable.

Every function guards against missing/invalid inputs and returns None rather
than raising, so callers can attach a quality flag instead of crashing.
"""

import math
from typing import Literal

import numpy as np
import pandas as pd

from app.config import settings

Zone = Literal["low", "grey", "high"]


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


def zone(fib4_val: float | None, age: float | None = None) -> Zone | None:
    """Map a FIB-4 value to a risk zone using thresholds from config.

    `age` is accepted for the >65 caveat noted in the plan but does not
    change the cutoffs here — standard adult cutoffs are used uniformly.
    """
    if fib4_val is None:
        return None
    if fib4_val < settings.fib4_low_max:
        return "low"
    if fib4_val > settings.fib4_high_min:
        return "high"
    return "grey"


def needs_age_caveat(age: float | None) -> bool:
    """True if FIB-4's standard cutoffs are less reliable for this patient's age."""
    return age is not None and age > settings.fib4_age_caveat_years


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

    zone_vals = pd.Series(
        np.select(
            [fib4_vals < settings.fib4_low_max, fib4_vals > settings.fib4_high_min],
            ["low", "high"],
            default="grey",
        ),
        index=df.index,
    )
    zone_vals = zone_vals.where(fib4_vals.notna(), None)

    out = df.copy()
    out["fib4"] = fib4_vals
    out["apri"] = apri_vals
    out["de_ritis"] = de_ritis_vals
    out["zone"] = zone_vals
    return out
