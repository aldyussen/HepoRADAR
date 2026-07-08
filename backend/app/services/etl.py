"""CSV ingest: fuzzy column matching, coercion, quality flags, upsert.

Liberal in what it accepts — bad individual values are dropped-and-flagged
rather than crashing the whole ingest; only rows missing a patient
identifier or a usable date are rejected outright.
"""

import datetime as dt
from collections import Counter
from typing import IO

import pandas as pd
from sqlalchemy.orm import Session

from app.models.lab import Lab
from app.models.patient import Patient
from app.schemas.ingest import IngestReport, RejectedRow
from app.services.loinc_map import ANALYTES, match_analyte, match_demographic

SEX_MAP = {
    "m": 1, "male": 1, "1": 1, "1.0": 1,
    "f": 0, "female": 0, "0": 0, "0.0": 0,
}


def _map_columns(columns: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Returns (demographic_col_map, analyte_col_map): canonical name -> raw column name."""
    demographic_map: dict[str, str] = {}
    analyte_map: dict[str, str] = {}
    for col in columns:
        demo_key = match_demographic(col)
        if demo_key and demo_key not in demographic_map:
            demographic_map[demo_key] = col
            continue
        analyte_key = match_analyte(col)
        if analyte_key and analyte_key not in analyte_map:
            analyte_map[analyte_key] = col
    return demographic_map, analyte_map


def _coerce_age(raw) -> int | None:
    if pd.isna(raw):
        return None
    try:
        age = int(float(raw))
    except (TypeError, ValueError):
        return None
    if age < 0 or age > 120:
        return None
    return age


def _coerce_sex(raw) -> int | None:
    if pd.isna(raw):
        return None
    return SEX_MAP.get(str(raw).strip().lower())


def _coerce_date(raw) -> dt.date | None:
    if pd.isna(raw):
        return None
    parsed = pd.to_datetime(raw, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _coerce_value(raw) -> float | None:
    if pd.isna(raw):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def ingest_csv(file: IO | str, db: Session) -> IngestReport:
    df = pd.read_csv(file)
    demographic_map, analyte_map = _map_columns(list(df.columns))

    rejected_rows: list[RejectedRow] = []
    quality_flags: Counter = Counter()
    touched_patient_ids: set[int] = set()
    labs_ingested = 0

    patient_id_col = demographic_map.get("patient_id")
    if patient_id_col is None:
        raise ValueError("Could not find a patient identifier column (e.g. 'patient_id' or 'mrn') in the CSV.")

    date_col = demographic_map.get("date")

    for row_index, row in df.iterrows():
        raw_mrn = row.get(patient_id_col)
        if pd.isna(raw_mrn) or str(raw_mrn).strip() == "":
            rejected_rows.append(RejectedRow(row_index=int(row_index), reason="missing patient identifier"))
            continue
        mrn = str(raw_mrn).strip()

        row_date = _coerce_date(row.get(date_col)) if date_col else None
        if row_date is None:
            rejected_rows.append(RejectedRow(row_index=int(row_index), reason="missing or unparseable date"))
            continue

        age = _coerce_age(row.get(demographic_map.get("age"))) if "age" in demographic_map else None
        sex = _coerce_sex(row.get(demographic_map.get("sex"))) if "sex" in demographic_map else None

        patient = db.query(Patient).filter(Patient.mrn == mrn).one_or_none()
        if patient is None:
            patient = Patient(mrn=mrn, age=age, sex=sex)
            db.add(patient)
            db.flush()
        else:
            if age is not None:
                patient.age = age
            if sex is not None:
                patient.sex = sex

        touched_patient_ids.add(patient.id)

        present_analytes = 0
        for analyte, raw_col in analyte_map.items():
            value = _coerce_value(row.get(raw_col))
            if value is None:
                continue
            present_analytes += 1

            low, high = ANALYTES[analyte]["range"]
            lab_quality_flag = None
            if value < low or value > high:
                quality_flags[f"{analyte}_out_of_range"] += 1
                lab_quality_flag = f"аномальное_значение"
                value = None

            existing_lab = (
                db.query(Lab)
                .filter(Lab.patient_id == patient.id, Lab.analyte == analyte, Lab.date == row_date)
                .one_or_none()
            )
            if existing_lab is None:
                db.add(
                    Lab(
                        patient_id=patient.id,
                        analyte=analyte,
                        loinc_code=ANALYTES[analyte]["loinc"],
                        value=value,
                        unit=ANALYTES[analyte]["unit"],
                        date=row_date,
                        source_label=raw_col,
                        quality_flag=lab_quality_flag,
                    )
                )
            else:
                existing_lab.value = value
                existing_lab.source_label = raw_col
                existing_lab.quality_flag = lab_quality_flag
            labs_ingested += 1

        for required in ("AST", "ALT", "PLT"):
            if required not in analyte_map or pd.isna(row.get(analyte_map.get(required))):
                quality_flags[f"missing_{required}"] += 1

    db.commit()

    return IngestReport(
        rows_processed=len(df),
        patients_ingested=len(touched_patient_ids),
        labs_ingested=labs_ingested,
        rows_rejected=len(rejected_rows),
        rejected_rows=rejected_rows,
        quality_flags=dict(quality_flags),
    )
