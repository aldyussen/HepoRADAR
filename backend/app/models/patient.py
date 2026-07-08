import datetime as dt

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mrn: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0/1 per feature contract

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    labs: Mapped[list["Lab"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    scores: Mapped[list["Score"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    referrals: Mapped[list["Referral"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    cascade_events: Mapped[list["CascadeEvent"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
