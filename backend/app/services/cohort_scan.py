import datetime as dt
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.lab import Lab
from app.models.patient import Patient
from app.models.score import Score
from app.schemas.cohort import ScanSummary
from app.services.ranking import is_lost
from app.services.scoring import score_dataframe
from app.services import ml_infer

REQUIRED_ANALYTES = ("AST", "ALT", "PLT")
OPTIONAL_ANALYTES = ("BILIRUBIN", "ALBUMIN")
ANALYTES_FOR_FEATURES = REQUIRED_ANALYTES + OPTIONAL_ANALYTES

def run_cohort_scan(db: Session) -> ScanSummary:
    patients = db.query(Patient).all()
    if not patients:
        return ScanSummary(total=0, low=0, grey=0, high=0, lost_count=0)

    patient_by_id = {p.id: p for p in patients}

    labs = (
        db.query(Lab.patient_id, Lab.analyte, Lab.value, Lab.date)
        .filter(Lab.analyte.in_(ANALYTES_FOR_FEATURES))
        .all()
    )
    if not labs:
        return ScanSummary(total=0, low=0, grey=0, high=0, lost_count=0)

    labs_df = pd.DataFrame(labs, columns=["patient_id", "analyte", "value", "date"])
    wide = labs_df.pivot_table(index=["patient_id", "date"], columns="analyte", values="value", aggfunc="first")
    wide = wide.reset_index()
    for analyte in ANALYTES_FOR_FEATURES:
        if analyte not in wide.columns:
            wide[analyte] = pd.NA

    complete = wide.dropna(subset=list(REQUIRED_ANALYTES)).copy()
    if complete.empty:
        return ScanSummary(total=0, low=0, grey=0, high=0, lost_count=0)

    complete["date"] = pd.to_datetime(complete["date"])
    latest = complete.sort_values("date").groupby("patient_id", as_index=False).last()

    latest["age"] = latest["patient_id"].map(lambda pid: patient_by_id[pid].age)
    latest["sex"] = latest["patient_id"].map(lambda pid: patient_by_id[pid].sex)
    latest = latest.rename(
        columns={"AST": "ast", "ALT": "alt", "PLT": "plt", "BILIRUBIN": "bilirubin", "ALBUMIN": "albumin"}
    )

    scored = score_dataframe(latest)

    scored["ml_risk"] = None
    grey_mask = scored["zone"] == "grey"
    if grey_mask.any():
        features_df = scored.loc[grey_mask, ["age", "sex", "ast", "alt", "plt", "bilirubin", "albumin"]].copy()
        features_df["diabetes"] = np.nan
        features_df["bmi"] = np.nan
        scored.loc[grey_mask, "ml_risk"] = ml_infer.predict_risk(features_df)

    reference_date = dt.date.today()
    scored["is_lost"] = scored.apply(
        lambda row: is_lost(row["zone"], row["date"].date(), reference_date, ml_risk=row["ml_risk"]), axis=1
    )

    new_scores = [
        Score(
            patient_id=int(row["patient_id"]),
            lab_date=row["date"].date(),
            fib4=None if pd.isna(row["fib4"]) else float(row["fib4"]),
            apri=None if pd.isna(row["apri"]) else float(row["apri"]),
            de_ritis=None if pd.isna(row["de_ritis"]) else float(row["de_ritis"]),
            zone=row["zone"],
            ml_risk=None if pd.isna(row["ml_risk"]) else float(row["ml_risk"]),
            is_lost=bool(row["is_lost"]),
        )
        for _, row in scored.iterrows()
    ]
    db.add_all(new_scores)
    db.commit()

    zone_counts = scored["zone"].value_counts()
    return ScanSummary(
        total=int(len(scored)),
        low=int(zone_counts.get("low", 0)),
        grey=int(zone_counts.get("grey", 0)),
        high=int(zone_counts.get("high", 0)),
        lost_count=int(scored["is_lost"].sum()),
    )
