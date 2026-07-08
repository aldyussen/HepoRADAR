from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.roles import Role, require_role
from app.models.patient import Patient
from app.services.cascade_logic import compute_reflex_flags

router = APIRouter(tags=["referral"])

@router.post(
    "/patients/{patient_id}/referral",
    dependencies=[Depends(require_role(Role.doctor, Role.admin))],
)
def generate_referral(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    flags = compute_reflex_flags(patient.labs)
    has_reflex = any(f["type"] == "HCV_RNA_MISSING" for f in flags)
    
    latest_score = max(patient.scores, key=lambda s: s.lab_date) if patient.scores else None
    
    zone_str = latest_score.zone if latest_score else "N/A"
    fib4_val = round(latest_score.fib4, 2) if latest_score and latest_score.fib4 is not None else "N/A"
    
    # Try LLM
    text = ""
    try:
        from app.services.llm_client import get_llm
        llm = get_llm()
        if llm:
            prompt = f"Сгенерируй направление к гепатологу для пациента {patient.mrn}, возраст {patient.age}, FIB-4 {fib4_val} (зона {zone_str})."
            if has_reflex:
                prompt += " Пациенту показан дозаказ ПЦР на HCV-RNA (Anti-HCV положительный)."
            # LLM is available but we might not have the actual completion setup ready in the backend
            # Fall back to template for safety and determinism.
    except Exception:
        pass
        
    if not text:
        # Fallback deterministic
        text = f"НАПРАВЛЕНИЕ К ГЕПАТОЛОГУ\n\n"
        text += f"Пациент: {patient.mrn}\n"
        text += f"Возраст: {patient.age or 'Не указан'}\n"
        text += f"Пол: {'М' if patient.sex == 1 else 'Ж' if patient.sex == 0 else 'Не указан'}\n\n"
        text += f"ПРИЧИНА НАПРАВЛЕНИЯ:\n"
        text += f"- Оценка риска фиброза (FIB-4): {fib4_val} (зона риска: {zone_str})\n"
        
        if has_reflex:
            text += f"- ВНИМАНИЕ: Выявлен положительный Anti-HCV, однако ПЦР на HCV-RNA не сдавался.\n"
            
        text += f"\nРЕКОМЕНДАЦИИ:\n"
        text += f"1. Консультация гепатолога\n"
        text += f"2. Проведение эластометрии печени (FibroScan)\n"
        if has_reflex:
            text += f"3. ДОЗАКАЗ: ПЦР на HCV-RNA (количественный)\n"
            
    return {"text": text}
