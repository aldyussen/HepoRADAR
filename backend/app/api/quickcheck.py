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
        
    f4 = fib4(payload.age, payload.ast, payload.alt, payload.plt)
    ap = apri(payload.ast, settings.ast_uln, payload.plt)
    dr = de_ritis(payload.ast, payload.alt)
    z = zone(f4, payload.age)
    
    msg = None
    if payload.age is not None and payload.age < 35:
        z = "n/a"
        msg = "FIB-4 не валидирован для пациентов младше 35 лет."
        
    reflex = False
    if payload.anti_hcv_pos is True and not payload.hcv_rna_done:
        reflex = True
        
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
        reflex_flag=reflex
    )
