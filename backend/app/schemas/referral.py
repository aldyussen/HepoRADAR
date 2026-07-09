import datetime as dt

from pydantic import BaseModel, ConfigDict


class ReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    status: str
    source: str
    content: str
    created_at: dt.datetime
