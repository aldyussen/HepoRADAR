from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.roles import Role, require_role
from app.db.session import get_db
from app.models.score import Score
from app.schemas.cohort import ScanSummary, WorklistItem, WorklistResponse
from app.services.ranking import rank_worklist
from app.services.cohort_scan import run_cohort_scan

router = APIRouter(prefix="/cohort", tags=["cohort"])


@router.post(
    "/scan",
    response_model=ScanSummary,
    dependencies=[Depends(require_role(Role.doctor, Role.admin))],
)
def scan(db: Session = Depends(get_db)) -> ScanSummary:
    return run_cohort_scan(db)



@router.get(
    "/worklist",
    response_model=WorklistResponse,
    dependencies=[Depends(require_role(Role.doctor, Role.admin, Role.viewer))],
)
def worklist(
    zone: str | None = Query(default=None),
    age_min: int | None = Query(default=None),
    marker: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> WorklistResponse:
    all_scores = db.query(Score).order_by(Score.patient_id, Score.computed_at.desc()).all()

    latest_by_patient: dict[int, Score] = {}
    for score in all_scores:
        if score.patient_id not in latest_by_patient:
            latest_by_patient[score.patient_id] = score

    candidates = []
    for score in latest_by_patient.values():
        if not score.is_lost:
            continue
        patient = score.patient

        if zone is not None and score.zone != zone:
            continue
        if age_min is not None and (patient.age is None or patient.age < age_min):
            continue
        if marker is not None and (score.quality_flags is None or marker not in score.quality_flags):
            continue
            
        candidates.append(
            {
                "patient_id": patient.id,
                "mrn": patient.mrn,
                "age": patient.age,
                "sex": patient.sex,
                "fib4": score.fib4,
                "apri": score.apri,
                "zone": score.zone,
                "ml_risk": score.ml_risk,
                "is_lost": score.is_lost,
                "last_lab_date": score.lab_date,
                "risk": score.fib4,
                "completeness": 1.0,
            }
        )

    ranked = rank_worklist(candidates)
    total = len(ranked)
    start = (page - 1) * page_size
    page_items = ranked[start : start + page_size]

    return WorklistResponse(
        items=[WorklistItem(**item) for item in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )
