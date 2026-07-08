import numpy as np
import pandas as pd
import pytest

from app.services import ml_infer
from ml.src.export import export_placeholder


def _reset_caches():
    ml_infer._cache.update(key=None, model=None, feature_order=None, available=False)
    ml_infer._explainer_cache.update(key=None, explainer=None, available=False)


@pytest.fixture(autouse=True)
def _no_artifacts_by_default(monkeypatch, tmp_path):
    _reset_caches()
    monkeypatch.setattr(ml_infer.settings, "model_path", str(tmp_path / "missing_model.pkl"))
    monkeypatch.setattr(ml_infer.settings, "feature_order_path", str(tmp_path / "missing_feature_order.json"))
    monkeypatch.setattr(ml_infer.settings, "shap_explainer_path", str(tmp_path / "missing_explainer.pkl"))
    yield
    _reset_caches()


def _row(**overrides):
    row = {
        "age": 50, "sex": 1, "ast": 30, "alt": 25, "plt": 200,
        "bilirubin": None, "albumin": None, "diabetes": None, "bmi": None,
    }
    row.update(overrides)
    return row


def test_is_available_false_without_artifacts():
    assert ml_infer.is_available() is False


def test_is_explainer_available_false_without_artifacts():
    assert ml_infer.is_explainer_available() is False


def test_predict_risk_falls_back_to_monotonic_fib4_transform():
    df = pd.DataFrame([
        _row(age=70, ast=120, alt=30, plt=60),  # high FIB-4
        _row(age=25, ast=20, alt=20, plt=250),  # low FIB-4
    ])
    risk = ml_infer.predict_risk(df)

    assert risk.shape == (2,)
    assert all(0.0 <= r <= 1.0 for r in risk)
    assert risk[0] > risk[1]  # monotonic: higher FIB-4 -> higher fallback risk


def test_predict_risk_uses_placeholder_model_when_present(monkeypatch, tmp_path):
    paths = export_placeholder(tmp_path / "artifacts")
    monkeypatch.setattr(ml_infer.settings, "model_path", str(paths["model"]))
    monkeypatch.setattr(ml_infer.settings, "feature_order_path", str(paths["feature_order"]))

    assert ml_infer.is_available() is True

    df = pd.DataFrame([_row()])
    risk = ml_infer.predict_risk(df)
    assert risk.shape == (1,)
    assert 0.0 <= risk[0] <= 1.0


def test_predict_risk_respects_feature_order(monkeypatch):
    monkeypatch.setattr(ml_infer, "load_model", lambda: None)
    received = {}

    class RecordingModel:
        def predict_proba(self, X):
            received["columns"] = list(X.columns)
            return np.column_stack([np.zeros(len(X)), np.full(len(X), 0.42)])

    ml_infer._cache.update(
        key="test", model=RecordingModel(), feature_order=["plt", "ast", "age"], available=True
    )

    df = pd.DataFrame([_row()])
    risk = ml_infer.predict_risk(df)

    assert received["columns"] == ["plt", "ast", "age"]
    assert risk[0] == pytest.approx(0.42)


def test_explain_row_without_explainer_uses_rule_based_reason():
    result = ml_infer.explain_row(_row(ast=80, plt=90, alt=20))
    assert result["base_value"] is None
    assert result["prediction"] is not None
    assert len(result["factors"]) > 0
    assert all(f["direction"] == "increases risk" for f in result["factors"])


def test_explain_row_with_placeholder_explainer(monkeypatch, tmp_path):
    paths = export_placeholder(tmp_path / "artifacts")
    monkeypatch.setattr(ml_infer.settings, "shap_explainer_path", str(paths["explainer"]))

    result = ml_infer.explain_row(_row(ast=80, plt=90, alt=20, bilirubin=1.0, albumin=3.8))

    assert result["base_value"] == pytest.approx(0.3)
    assert len(result["factors"]) <= 3
    assert all({"feature", "value", "shap", "direction"} <= f.keys() for f in result["factors"])
