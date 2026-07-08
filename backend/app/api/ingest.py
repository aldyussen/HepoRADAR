from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ingest import IngestReport
from app.services.etl import ingest_csv

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestReport)
def ingest(file: UploadFile, db: Session = Depends(get_db)) -> IngestReport:
    try:
        return ingest_csv(file.file, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
