import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Referral(Base):
    __tablename__ = "referral"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)  # draft | sent | template_fallback
    source: Mapped[str] = mapped_column(String, default="template", nullable=False)  # llm | template
    content: Mapped[str] = mapped_column(Text, nullable=False)  # rendered referral text / JSON

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="referrals")
