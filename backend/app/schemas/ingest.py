from pydantic import BaseModel


class RejectedRow(BaseModel):
    row_index: int
    reason: str


class IngestReport(BaseModel):
    rows_processed: int
    patients_ingested: int
    labs_ingested: int
    rows_rejected: int
    rejected_rows: list[RejectedRow]
    quality_flags: dict[str, int]
