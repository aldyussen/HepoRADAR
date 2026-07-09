from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.roles import Role, require_role
from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.referral import ReferralResponse
from app.services import ml_infer
from app.services.referral import build_referral
from app.services.scoring import apri as compute_apri
from app.services.scoring import fib4, rule_based_factors
from app.services.scoring import zone as compute_zone
from app.config import settings

router = APIRouter(prefix="/patients", tags=["referral"])

REQUIRED_ANALYTES = ("AST", "ALT", "PLT")
OPTIONAL_ANALYTES = ("BILIRUBIN", "ALBUMIN")


def _latest_scores_and_factors(patient: Patient) -> tuple[dict, list[dict]]:
    """Same latest-complete-labs selection as `/patients/{id}/explain`, reused
    here so the referral cites the same scores/factors the explain card shows.
    """
    labs_by_date: dict = {}
    for lab in patient.labs:
        if lab.analyte not in REQUIRED_ANALYTES + OPTIONAL_ANALYTES:
            continue
        labs_by_date.setdefault(lab.date, {})[lab.analyte] = lab.value

    complete_dates = [d for d, values in labs_by_date.items() if all(a in values for a in REQUIRED_ANALYTES)]
    if not complete_dates:
        return {"fib4": None, "apri": None, "zone": None, "ml_risk": None}, []

    latest_labs = labs_by_date[max(complete_dates)]
    features_row = {
        "age": patient.age,
        "sex": patient.sex,
        "ast": latest_labs.get("AST"),
        "alt": latest_labs.get("ALT"),
        "plt": latest_labs.get("PLT"),
        "bilirubin": latest_labs.get("BILIRUBIN"),
        "albumin": latest_labs.get("ALBUMIN"),
        "diabetes": None,
        "bmi": None,
    }

    fib4_val = fib4(features_row["age"], features_row["ast"], features_row["alt"], features_row["plt"])
    apri_val = compute_apri(features_row["ast"], settings.ast_uln, features_row["plt"])
    patient_zone = compute_zone(fib4_val)

    if patient_zone == "grey":
        explained = ml_infer.explain_row(features_row)
        ml_risk = explained["prediction"]
        factors = explained["factors"]
    else:
        ml_risk = None
        factors = rule_based_factors(features_row)

    scores = {"fib4": fib4_val, "apri": apri_val, "zone": patient_zone, "ml_risk": ml_risk}
    return scores, factors


@router.post(
    "/{patient_id}/referral",
    response_model=ReferralResponse,
    dependencies=[Depends(require_role(Role.doctor, Role.admin))],
)
def create_referral(patient_id: int, db: Session = Depends(get_db)) -> ReferralResponse:
    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    scores, factors = _latest_scores_and_factors(patient)
    return build_referral(db, patient, scores, factors)
