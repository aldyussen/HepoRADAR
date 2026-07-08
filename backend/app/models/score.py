import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Score(Base):
    __tablename__ = "score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), nullable=False, index=True)

    lab_date: Mapped[dt.date] = mapped_column(Date, nullable=False)  # date of the lab set this score is based on

    fib4: Mapped[float | None] = mapped_column(Float, nullable=True)
    apri: Mapped[float | None] = mapped_column(Float, nullable=True)
    de_ritis: Mapped[float | None] = mapped_column(Float, nullable=True)
    zone: Mapped[str | None] = mapped_column(String, nullable=True)  # low | grey | high

    ml_risk: Mapped[float | None] = mapped_column(Float, nullable=True)  # populated in B2
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_flags: Mapped[str | None] = mapped_column(String, nullable=True)  # comma-separated flags

    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="scores")
