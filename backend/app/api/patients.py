from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.roles import Role, require_role
from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCard

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get(
    "/{patient_id}",
    response_model=PatientCard,
    dependencies=[Depends(require_role(Role.doctor, Role.admin))],
)
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientCard:
    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    labs = sorted(patient.labs, key=lambda lab: lab.date)
    scores = sorted(patient.scores, key=lambda score: score.lab_date)

    from app.services.cascade_logic import compute_reflex_flags
    reflex_flags = compute_reflex_flags(labs)

    return PatientCard(
        id=patient.id,
        mrn=patient.mrn,
        age=patient.age,
        sex=patient.sex,
        labs=labs,
        scores=scores,
        reflex_flags=reflex_flags,
    )
