import datetime as dt

from pydantic import BaseModel, ConfigDict


class LabEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analyte: str
    value: float | None
    unit: str | None
    date: dt.date
    quality_flag: str | None


class ScoreEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lab_date: dt.date
    fib4: float | None
    apri: float | None
    de_ritis: float | None
    zone: str | None
    ml_risk: float | None
    is_lost: bool
    quality_flags: str | None
    computed_at: dt.datetime


class PatientCard(BaseModel):
    id: int
    mrn: str
    age: int | None
    sex: int | None
    labs: list[LabEntry]
    scores: list[ScoreEntry]
