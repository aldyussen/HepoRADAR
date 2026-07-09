from typing import List

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.services.llm_client import extract_labs_from_images
from app.services.scoring import apri, de_ritis, fib4, rule_based_factors, zone
from app.config import settings

router = APIRouter(prefix="/quick", tags=["quickcheck"])

class QuickCheckValues(BaseModel):
    age: int | None = None
    sex: int | None = None
    ast: float | None = None
    alt: float | None = None
    plt: float | None = None
    anti_hcv_pos: bool | None = None
    hcv_rna_done: bool | None = None

class QuickCheckResponse(BaseModel):
    status: str
    message: str | None = None
    missing: list[str] = []
    fib4: float | None = None
    apri: float | None = None
    de_ritis: float | None = None
    zone: str | None = None
    factors: list[dict] = []
    reflex_flag: bool = False
    critical_flags: list[str] = []
    warnings: list[str] = []

@router.post("/extract")
async def extract_labs(files: List[UploadFile] = File(...)):
    """Extract lab values from uploaded images using Gemini Vision."""
    image_bytes_list = []
    mime_types = []
    
    for file in files:
        if file.content_type.startswith("image/"):
            content = await file.read()
            image_bytes_list.append(content)
            mime_types.append(file.content_type)
            
    if not image_bytes_list:
        return {"status": "unreadable", "hint": "Please upload an image."}

    try:
        extracted = extract_labs_from_images(image_bytes_list, mime_types)
        return extracted
    except Exception as e:
        return {"status": "error", "hint": str(e)}

@router.post("/check", response_model=QuickCheckResponse)
def check_labs(payload: QuickCheckValues):
    """Calculate scores and return zone + reflex logic."""
    missing = []
    if payload.ast is None: missing.append("АСТ")
    if payload.alt is None: missing.append("АЛТ")
    if payload.plt is None: missing.append("Тромбоциты (PLT)")
    
    if missing:
        return QuickCheckResponse(
            status="incomplete",
            missing=missing,
            message=f"Дозакажите: {', '.join(missing)}"
        )
        
    # Validation checks
    invalid_fields = []
    if payload.age is not None and not (0 <= payload.age <= 120):
        invalid_fields.append("Возраст")
    if payload.ast is not None and not (0 <= payload.ast <= 5000):
        invalid_fields.append("АСТ")
    if payload.alt is not None and not (0 <= payload.alt <= 5000):
        invalid_fields.append("АЛТ")
    if payload.plt is not None and payload.plt > 1000:
        invalid_fields.append("Тромбоциты (указаны в абсолютных значениях? Ожидается 10^9/л)")
    elif payload.plt is not None and not (1 <= payload.plt <= 1000):
        invalid_fields.append("Тромбоциты (PLT)")
        
    if invalid_fields:
        return QuickCheckResponse(
            status="invalid",
            message=f"Проверьте значение {', '.join(invalid_fields)}"
        )
        
    critical_flags = []
    if payload.plt is not None and payload.plt < 50:
        critical_flags.append("Критически низкие тромбоциты")
    if (payload.ast is not None and payload.ast > 1000) or (payload.alt is not None and payload.alt > 1000):
        critical_flags.append("Критическое поражение печени")
        
    f4 = fib4(payload.age, payload.ast, payload.alt, payload.plt)
    ap = apri(payload.ast, settings.ast_uln, payload.plt)
    dr = de_ritis(payload.ast, payload.alt)
    z = zone(f4, payload.age, payload.ast, payload.alt)
    
    msg = None
    warnings = []
    
    # 1. Age-based warnings
    if payload.age is not None:
        if payload.age < 18:
            msg = "FIB-4 не применяется в педиатрии (<18 лет)."
        elif payload.age < 35:
            msg = "FIB-4 не валидирован для пациентов младше 35 лет."
        elif payload.age >= 65:
            warnings.append("Для пациентов ≥65 лет используется адаптированный нижний порог FIB-4 (2.0 вместо 1.3), чтобы избежать ложноположительных результатов.")
            
    # 2. Acute liver injury warning
    if (payload.ast is not None and payload.ast > 500) or (payload.alt is not None and payload.alt > 500):
        msg = "FIB-4 не применим при острых повреждениях печени (АСТ/АЛТ > 500)."
        
    if critical_flags:
        z = "critical"
        
    # 3. Clinical traps warnings
    if z in ["high", "grey"] and payload.plt is not None and payload.plt < 100:
        warnings.append("Сниженные тромбоциты могут быть не связаны с печенью (ИТП, химиотерапия, болезни крови) — возможен ложно-завышенный FIB-4.")
        
    if z in ["high", "grey"] and dr is not None and dr > 2:
        warnings.append("Коэффициент де Ритиса (АСТ/АЛТ) > 2. Часто указывает на алкогольную этиологию или выраженный цирроз.")
        
    # 4. Reflex and SVR warnings
    reflex = False
    if payload.anti_hcv_pos is True:
        if not payload.hcv_rna_done:
            reflex = True
            warnings.append("У пациента анти-HCV (+), но нет подтверждающего ПЦР на РНК ВГС. Требуется дозаказ.")
        else:
            warnings.append("Если пациент ранее получал лечение и достиг УВО, антитела остаются пожизненно.")
        
    factors = rule_based_factors({
        "ast": payload.ast,
        "alt": payload.alt,
        "plt": payload.plt,
        "age": payload.age
    })
    
    return QuickCheckResponse(
        status="ok",
        message=msg,
        fib4=f4,
        apri=ap,
        de_ritis=dr,
        zone=z,
        factors=factors,
        reflex_flag=reflex,
        critical_flags=critical_flags,
        warnings=warnings
    )
