import datetime as dt

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lab(Base):
    """One row per (patient, analyte, date) — long format survives messy input."""

    __tablename__ = "lab"
    __table_args__ = (UniqueConstraint("patient_id", "analyte", "date", name="uq_lab_patient_analyte_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), nullable=False, index=True)

    analyte: Mapped[str] = mapped_column(String, nullable=False, index=True)  # canonical name, e.g. "AST"
    loinc_code: Mapped[str | None] = mapped_column(String, nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    source_label: Mapped[str | None] = mapped_column(String, nullable=True)  # raw column name as ingested
    quality_flag: Mapped[str | None] = mapped_column(String, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="labs")
