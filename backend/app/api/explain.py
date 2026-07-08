from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.explain import ExplainResponse
from app.services import ml_infer
from app.services.scoring import fib4, fib4_to_risk, rule_based_factors
from app.services.scoring import zone as compute_zone

router = APIRouter(prefix="/patients", tags=["explain"])

REQUIRED_ANALYTES = ("AST", "ALT", "PLT")
OPTIONAL_ANALYTES = ("BILIRUBIN", "ALBUMIN")


@router.get("/{patient_id}/explain", response_model=ExplainResponse)
def explain(patient_id: int, db: Session = Depends(get_db)) -> ExplainResponse:
    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    labs_by_date: dict = {}
    for lab in patient.labs:
        if lab.analyte not in REQUIRED_ANALYTES + OPTIONAL_ANALYTES:
            continue
        labs_by_date.setdefault(lab.date, {})[lab.analyte] = lab.value

    complete_dates = [d for d, values in labs_by_date.items() if all(a in values for a in REQUIRED_ANALYTES)]
    if not complete_dates:
        return ExplainResponse(base_value=None, prediction=None, factors=[])

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
    patient_zone = compute_zone(fib4_val)

    # Grey-zone gating: only ambiguous FIB-4 cases go through the ML explainer.
    # Low/high already have a confident rule-based score — same as `/cohort/scan`.
    if patient_zone == "grey":
        result = ml_infer.explain_row(features_row)
    else:
        result = {
            "base_value": None,
            "prediction": fib4_to_risk(fib4_val),
            "factors": rule_based_factors(features_row),
        }

    return ExplainResponse(**result)
