import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CascadeEvent(Base):
    """HCV care-cascade stage event: screened -> anti_hcv_positive -> rna_tested -> treated -> svr."""

    __tablename__ = "cascade_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), nullable=False, index=True)

    stage: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="cascade_events")
