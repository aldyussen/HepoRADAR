"""Writes a trivial placeholder model + SHAP-explainer artifact.

This is NOT a trained model — real training happens in train.py once the
org's data lands (M2/M4 in the plan). This exists purely so the backend's
`ml_infer.py` "model present" / "explainer present" code paths are testable
before that. Both classes are deterministic, fixed-weight stand-ins with the
exact call shape (`predict_proba`, `shap_values`) the real artifacts will have.
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

# Exact feature contract (Part 0.2 of the plan / CLAUDE.md), fixed order.
FEATURE_ORDER = ["age", "sex", "ast", "alt", "plt", "bilirubin", "albumin", "diabetes", "bmi"]

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "artifacts"


class PlaceholderModel:
    """Deterministic stand-in for the real grey-zone classifier.

    Fixed, clinically-plausible-direction linear score (AST/bilirubin up =
    riskier, platelets/albumin up = safer) squashed through a sigmoid — not
    trained on data, just enough to exercise the model-loaded code path.
    """

    def __init__(self, feature_order: list[str]):
        self.feature_order = feature_order

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X = X[self.feature_order].astype(float)
        score = (
            0.03 * X["ast"].fillna(30)
            + 0.2 * X["bilirubin"].fillna(0.8)
            - 0.02 * X["plt"].fillna(200)
            - 0.3 * X["albumin"].fillna(4.0)
        )
        risk = 1 / (1 + np.exp(-0.05 * score))
        return np.column_stack([1 - risk, risk])


class PlaceholderExplainer:
    """Deterministic stand-in for shap.TreeExplainer — same call shape, fixed weights."""

    expected_value = 0.3

    def __init__(self, feature_order: list[str]):
        self.feature_order = feature_order
        self.weights = {
            "ast": 0.01,
            "alt": 0.002,
            "plt": -0.004,
            "bilirubin": 0.15,
            "albumin": -0.2,
            "age": 0.005,
            "sex": 0.0,
            "diabetes": 0.05,
            "bmi": 0.01,
        }

    def shap_values(self, X: pd.DataFrame) -> np.ndarray:
        X = X[self.feature_order].astype(float)
        return np.column_stack([X[feat].fillna(0) * self.weights[feat] for feat in self.feature_order])


def export_placeholder(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "greyzone_model.pkl"
    explainer_path = output_dir / "shap_explainer.pkl"
    feature_order_path = output_dir / "feature_order.json"

    with open(model_path, "wb") as f:
        pickle.dump(PlaceholderModel(FEATURE_ORDER), f)
    with open(explainer_path, "wb") as f:
        pickle.dump(PlaceholderExplainer(FEATURE_ORDER), f)
    with open(feature_order_path, "w") as f:
        json.dump(FEATURE_ORDER, f)

    return {"model": model_path, "explainer": explainer_path, "feature_order": feature_order_path}


if __name__ == "__main__":
    paths = export_placeholder()
    print(f"Wrote placeholder artifacts to {paths['model'].parent}")
