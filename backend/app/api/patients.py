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
    db_scores = {s.lab_date: s for s in patient.scores}

    import datetime as dt

    import pandas as pd
    from app.services.scoring import score_dataframe
    from app.schemas.patient import ScoreEntry

    now = dt.datetime.now(dt.timezone.utc)
    scores_dict = {}
    labs_data = [{"analyte": l.analyte, "value": l.value, "date": l.date} for l in labs if l.analyte in ("AST", "ALT", "PLT", "BILIRUBIN", "ALBUMIN")]
    
    if labs_data:
        df = pd.DataFrame(labs_data)
        df["date"] = pd.to_datetime(df["date"])
        # Pivot so each date is a row with all analytes as columns
        wide = df.pivot_table(index="date", columns="analyte", values="value").reset_index()
        
        # Ensure all required columns exist for score_dataframe
        for col in ("AST", "ALT", "PLT", "BILIRUBIN", "ALBUMIN"):
            if col not in wide.columns:
                wide[col] = pd.NA
                
        wide["age"] = patient.age
        wide["sex"] = patient.sex
        wide = wide.rename(columns={"AST": "ast", "ALT": "alt", "PLT": "plt", "BILIRUBIN": "bilirubin", "ALBUMIN": "albumin"})
        
        scored = score_dataframe(wide)
        
        for _, row in scored.iterrows():
            d = row["date"].date()
            db_s = db_scores.get(d)
            scores_dict[d] = ScoreEntry(
                lab_date=d,
                fib4=None if pd.isna(row["fib4"]) else float(row["fib4"]),
                apri=None if pd.isna(row["apri"]) else float(row["apri"]),
                de_ritis=None if pd.isna(row["de_ritis"]) else float(row["de_ritis"]),
                zone=row["zone"] if pd.notna(row["zone"]) else None,
                ml_risk=db_s.ml_risk if db_s else None,
                is_lost=db_s.is_lost if db_s else False,
                quality_flags=str(row["quality_flags"]) if pd.notna(row["quality_flags"]) else "",
                computed_at=db_s.computed_at if db_s else now,
            )

    # Add any db scores that were missed (if any)
    for d, s in db_scores.items():
        if d not in scores_dict:
            scores_dict[d] = ScoreEntry(
                lab_date=s.lab_date,
                fib4=s.fib4,
                apri=s.apri,
                de_ritis=s.de_ritis,
                zone=s.zone,
                ml_risk=s.ml_risk,
                is_lost=s.is_lost,
                quality_flags=s.quality_flags or "",
                computed_at=s.computed_at,
            )

    scores = sorted(scores_dict.values(), key=lambda s: s.lab_date)

    return PatientCard(
        id=patient.id,
        mrn=patient.mrn,
        age=patient.age,
        sex=patient.sex,
        labs=labs,
        scores=scores,
    )
