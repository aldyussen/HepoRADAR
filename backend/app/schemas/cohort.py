import datetime as dt

from pydantic import BaseModel


class ScanSummary(BaseModel):
    total: int
    low: int
    grey: int
    high: int
    lost_count: int


class WorklistItem(BaseModel):
    patient_id: int
    mrn: str
    age: int | None
    sex: int | None
    fib4: float | None
    apri: float | None
    zone: str | None
    ml_risk: float | None
    is_lost: bool
    last_lab_date: dt.date | None


class WorklistResponse(BaseModel):
    items: list[WorklistItem]
    total: int
    page: int
    page_size: int
