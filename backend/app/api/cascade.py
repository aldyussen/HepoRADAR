from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.roles import Role, require_role
from app.db.session import get_db
from app.models.cascade_event import CascadeEvent
from app.models.patient import Patient
from app.schemas.cascade import CascadeFunnelResponse, ReflexFlaggedPatient
from app.services.cascade_logic import cascade_funnel, reflex_flag

router = APIRouter(prefix="/cascade", tags=["cascade"])


@router.get(
    "/hcv",
    response_model=CascadeFunnelResponse,
    dependencies=[Depends(require_role(Role.coordinator, Role.admin))],
)
def hcv_cascade(db: Session = Depends(get_db)) -> CascadeFunnelResponse:
    patients = db.query(Patient).all()

    stages_by_patient: dict[int, list[str]] = {patient.id: [] for patient in patients}
    events = db.query(CascadeEvent.patient_id, CascadeEvent.stage).all()
    for patient_id, stage in events:
        stages_by_patient.setdefault(patient_id, []).append(stage)

    funnel = cascade_funnel(list(stages_by_patient.values()))

    reflex_flagged = [
        ReflexFlaggedPatient(patient_id=patient.id, mrn=patient.mrn)
        for patient in patients
        if reflex_flag(stages_by_patient.get(patient.id, []))
    ]

    return CascadeFunnelResponse(funnel=funnel, reflex_flagged=reflex_flagged)
