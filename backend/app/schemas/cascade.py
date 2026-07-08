from pydantic import BaseModel


class ReflexFlaggedPatient(BaseModel):
    patient_id: int
    mrn: str


class CascadeFunnelResponse(BaseModel):
    funnel: dict[str, int]
    reflex_flagged: list[ReflexFlaggedPatient]
