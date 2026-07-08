from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]  # backend/app/config.py -> repo root

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HEPARADAR_", extra="ignore")

    database_url: str = "postgresql+psycopg://heparadar:heparadar@localhost:5432/heparadar"

    cors_origins: list[str] = ["http://localhost:5173"]

    # FIB-4 / APRI zone thresholds (Part 0.3 of the plan)
    fib4_low_max: float = 1.3
    fib4_high_min: float = 2.67
    apri_high_min: float = 1.0
    fib4_age_caveat_years: int = 65
    ast_uln: float = 40.0  # AST upper limit of normal (U/L), used by APRI

    # "Lost" patient definition (Part 0.1 fallback)
    lost_no_repeat_months: int = 6
    ml_risk_threshold: float = 0.5

    # ML artifact interface (Part 0.4 / B2)
    model_path: str = str(_REPO_ROOT / "ml" / "models" / "greyzone_model.pkl")
    shap_explainer_path: str = str(_REPO_ROOT / "ml" / "models" / "shap_explainer.pkl")
    feature_order_path: str = str(_REPO_ROOT / "ml" / "models" / "feature_order.json")

    # LLM / RAG (B3)
    llm_url: str = ""

    # Auth (B5)
    jwt_secret: str = "change-me-in-prod-this-default-is-not-secret-32bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14


settings = Settings()
