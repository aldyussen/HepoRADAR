from pydantic import BaseModel


class ExplainFactor(BaseModel):
    feature: str
    value: float | None
    shap: float | None
    direction: str


class ExplainResponse(BaseModel):
    base_value: float | None
    prediction: float | None
    factors: list[ExplainFactor]
