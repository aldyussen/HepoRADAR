from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.auth.roles import Role, require_role
from app.models.patient import Patient
from app.services.cascade_logic import compute_reflex_flags

router = APIRouter(tags=["cascade"])

class CascadeStage(BaseModel):
    stage: str
    count: int
    description: str

@router.get(
    "/patients/{patient_id}/reflex",
    dependencies=[Depends(require_role(Role.doctor, Role.admin))],
)
def get_patient_reflex(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    flags = compute_reflex_flags(patient.labs)
    return {"flags": flags}

@router.get(
    "/cascade/hcv",
    response_model=list[CascadeStage],
    dependencies=[Depends(require_role(Role.coordinator, Role.admin, Role.doctor, Role.viewer))],
)
def get_hcv_cascade(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    total_patients = len(patients)
    
    tested_anti_hcv = set()
    anti_hcv_pos = set()
    tested_rna = set()
    rna_pos = set()
    
    for p in patients:
        labs = p.labs
        has_anti_hcv = False
        has_anti_hcv_pos = False
        has_rna = False
        has_rna_pos = False
        
        for lab in labs:
            analyte = (lab.analyte or "").upper()
            val_str = str(lab.value).lower() if lab.value is not None else ""
            is_pos = val_str in ("1", "1.0", "positive", "pos", "+", "положит", "true") or (lab.value and float(lab.value) > 0)
            
            if analyte == "ANTI_HCV" or "ANTI-HCV" in analyte or "HCV AB" in analyte or "HCV_AB" in analyte:
                has_anti_hcv = True
                if is_pos:
                    has_anti_hcv_pos = True
                    
            if analyte == "HCV_RNA" or "HCV RNA" in analyte or "HCV-RNA" in analyte or "РНК" in analyte.upper():
                has_rna = True
                if is_pos:
                    has_rna_pos = True
                    
        if has_anti_hcv:
            tested_anti_hcv.add(p.id)
        if has_anti_hcv_pos:
            anti_hcv_pos.add(p.id)
        if has_rna:
            tested_rna.add(p.id)
        if has_rna_pos:
            rna_pos.add(p.id)
            
    return [
        CascadeStage(stage="Total Cohort", count=total_patients, description="Всего пациентов в базе"),
        CascadeStage(stage="Tested Anti-HCV", count=len(tested_anti_hcv), description="Сдали скрининг (Anti-HCV)"),
        CascadeStage(stage="Anti-HCV (+)", count=len(anti_hcv_pos), description="Положительный Anti-HCV"),
        CascadeStage(stage="Reflex / Tested RNA", count=len(tested_rna.intersection(anti_hcv_pos)), description="Сдали ПЦР (HCV-RNA) после (+) скрининга"),
        CascadeStage(stage="HCV-RNA (+)", count=len(rna_pos.intersection(anti_hcv_pos)), description="Подтвержденный диагноз ХВГ"),
    ]
