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
    labs_df["date"] = pd.to_datetime(labs_df["date"])
    labs_df = labs_df.sort_values(["patient_id", "date"])

    # Keep the latest of each analyte per patient
    latest_labs = labs_df.drop_duplicates(subset=["patient_id", "analyte"], keep="last")

    wide = latest_labs.pivot(index="patient_id", columns="analyte", values="value").reset_index()

    for analyte in ANALYTES_FOR_FEATURES:
        if analyte not in wide.columns:
            wide[analyte] = pd.NA

    # Also compute date difference
    dates_wide = latest_labs.pivot(index="patient_id", columns="analyte", values="date").reset_index()
    # Find min and max date among required analytes
    req_cols = [c for c in REQUIRED_ANALYTES if c in dates_wide.columns]
    dates_wide["min_date"] = dates_wide[req_cols].min(axis=1)
    dates_wide["max_date"] = dates_wide[req_cols].max(axis=1)
    dates_wide["date_diff"] = (dates_wide["max_date"] - dates_wide["min_date"]).dt.days
    dates_wide["date"] = dates_wide["max_date"]

    complete = pd.merge(wide, dates_wide[["patient_id", "date", "date_diff"]], on="patient_id")

    if complete.empty:
        return ScanSummary(total=0, low=0, grey=0, high=0, lost_count=0)

    complete["age"] = complete["patient_id"].map(lambda pid: patient_by_id[pid].age)
    complete["sex"] = complete["patient_id"].map(lambda pid: patient_by_id[pid].sex)
    complete = complete.rename(
        columns={"AST": "ast", "ALT": "alt", "PLT": "plt", "BILIRUBIN": "bilirubin", "ALBUMIN": "albumin"}
    )

    scored = score_dataframe(complete)
    
    # Add quality flags for date differences > 90 days
    mask_diff = complete["date_diff"] > 90
    if mask_diff.any():
        for idx in complete[mask_diff].index:
            current = scored.at[idx, "quality_flags"]
            flag = "разные_даты_анализов"
            scored.at[idx, "quality_flags"] = flag if not current else f"{current}, {flag}"
            
    # Add quality flags for missing analytes (or nullified due to anomaly)
    for req in ("ast", "alt", "plt"):
        mask_missing = complete[req].isna()
        if mask_missing.any():
            for idx in complete[mask_missing].index:
                current = scored.at[idx, "quality_flags"]
                flag = f"нет_{req.upper()}_или_аномалия"
                scored.at[idx, "quality_flags"] = flag if not current else f"{current}, {flag}"

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
