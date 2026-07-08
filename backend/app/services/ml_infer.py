"""ML integration seam: lazy-loads the grey-zone model + SHAP explainer.

Mandatory fallback (golden rule): a missing or broken artifact never raises —
callers always get a usable risk score / explanation, just without the
model's AUC bump. Callers are responsible for the grey-zone gate: only invoke
this module for patients whose FIB-4 zone is "grey" — low/high already have a
confident rule-based score and should never reach `predict_risk`.
"""

import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from app.config import settings
from app.services.scoring import fib4, fib4_to_risk, rule_based_factors

logger = logging.getLogger(__name__)

# backend/app/services/ml_infer.py -> repo root (sibling of `ml/`)
_REPO_ROOT = Path(__file__).resolve().parents[3]

_cache: dict = {"key": None, "model": None, "feature_order": None, "available": False}
_explainer_cache: dict = {"key": None, "explainer": None, "available": False}

_SEX_MAP = {"m": 1, "male": 1, "f": 0, "female": 0}


def _coerce_features(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerce a model-input frame's columns to numeric float64.

    Shared by `predict_risk` and `explain_row` so every caller feeds the
    model the same dtypes the training pipeline used (CLAUDE.md: never let
    train and infer diverge) — this is the single place that conversion
    happens, not duplicated per-router. `sex` is mapped to {0,1} if it
    arrives as a string; every other stray non-numeric (e.g. an all-missing
    optional lab column, which pandas types as `object`) is coerced with
    `errors="coerce"` into NaN. That's safe because the model is NaN-native
    (XGBoost) — do not median-impute here.
    """
    df = df.copy()
    if "sex" in columns and "sex" in df.columns and not pd.api.types.is_numeric_dtype(df["sex"]):
        df["sex"] = df["sex"].astype(str).str.strip().str.lower().map(_SEX_MAP)
    df[columns] = df[columns].apply(pd.to_numeric, errors="coerce").astype("float64")
    return df


def _ensure_repo_root_on_path() -> None:
    repo_root_str = str(_REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def load_model() -> None:
    """Lazy-load the model + feature order; cached until the configured paths change."""
    model_path = Path(settings.model_path)
    feature_order_path = Path(settings.feature_order_path)
    cache_key = (str(model_path), str(feature_order_path))
    if _cache["key"] == cache_key:
        return
    _cache.update(key=cache_key, model=None, feature_order=None, available=False)

    if not model_path.exists() or not feature_order_path.exists():
        logger.warning("ML model artifact not found at %s — falling back to FIB-4-based risk.", model_path)
        return

    try:
        _ensure_repo_root_on_path()
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(feature_order_path) as f:
            feature_order = json.load(f)
        _cache.update(model=model, feature_order=feature_order, available=True)
    except Exception:
        logger.exception("Failed to load ML model from %s — falling back to FIB-4-based risk.", model_path)
        _cache.update(model=None, feature_order=None, available=False)


def is_available() -> bool:
    load_model()
    return _cache["available"]


def _fallback_risk(features_df: pd.DataFrame) -> np.ndarray:
    def _row_risk(row) -> float:
        risk = fib4_to_risk(fib4(row.get("age"), row.get("ast"), row.get("alt"), row.get("plt")))
        return risk if risk is not None else 0.5

    return features_df.apply(_row_risk, axis=1).to_numpy(dtype=float)


def predict_risk(features_df: pd.DataFrame) -> np.ndarray:
    """Risk in [0, 1] per row: model if loaded, else a monotonic FIB-4 transform.

    `features_df` must carry the feature-contract columns (age, sex, ast, alt,
    plt, bilirubin, albumin, diabetes, bmi) — extra/missing optional columns
    are fine, the fallback only needs age/ast/alt/plt.
    """
    load_model()
    if not _cache["available"]:
        return _fallback_risk(features_df)

    ordered = _coerce_features(features_df[_cache["feature_order"]], _cache["feature_order"])
    proba = np.asarray(_cache["model"].predict_proba(ordered))
    return proba[:, 1]


def load_explainer() -> None:
    """Lazy-load the SHAP explainer; cached until the configured path changes."""
    explainer_path = Path(settings.shap_explainer_path)
    cache_key = str(explainer_path)
    if _explainer_cache["key"] == cache_key:
        return
    _explainer_cache.update(key=cache_key, explainer=None, available=False)

    if not explainer_path.exists():
        return

    try:
        _ensure_repo_root_on_path()
        with open(explainer_path, "rb") as f:
            explainer = pickle.load(f)
        _explainer_cache.update(explainer=explainer, available=True)
    except Exception:
        logger.exception("Failed to load SHAP explainer from %s — falling back to rule-based reason.", explainer_path)
        _explainer_cache.update(explainer=None, available=False)


def is_explainer_available() -> bool:
    load_explainer()
    return _explainer_cache["available"]


def explain_row(features_row: dict) -> dict:
    """SHAP factors for one patient if an explainer is loaded, else a rule-based reason.

    Returns the `/explain` payload shape:
    {"base_value": ..., "prediction": ..., "factors": [{"feature", "value", "shap", "direction"}]}
    Never raises — an explainer error falls through to the rule-based reason.
    """
    load_explainer()
    if _explainer_cache["available"]:
        try:
            explainer = _explainer_cache["explainer"]
            order = getattr(explainer, "feature_order", None) or list(features_row.keys())
            row_df = pd.DataFrame([{k: features_row.get(k) for k in order}])
            row_df = _coerce_features(row_df, order)
            contributions = np.asarray(explainer.shap_values(row_df))[0]
            base_value = float(getattr(explainer, "expected_value", 0.0))
            factors = sorted(
                (
                    {
                        "feature": feat,
                        "value": features_row.get(feat),
                        "shap": float(shap_val),
                        "direction": "increases risk" if shap_val >= 0 else "decreases risk",
                    }
                    for feat, shap_val in zip(order, contributions)
                ),
                key=lambda f: abs(f["shap"]),
                reverse=True,
            )[:3]
            return {"base_value": base_value, "prediction": base_value + float(contributions.sum()), "factors": factors}
        except Exception:
            logger.exception("SHAP explainer failed — falling back to rule-based reason.")

    fib4_val = fib4(features_row.get("age"), features_row.get("ast"), features_row.get("alt"), features_row.get("plt"))
    return {
        "base_value": None,
        "prediction": fib4_to_risk(fib4_val),
        "factors": rule_based_factors(features_row),
    }
