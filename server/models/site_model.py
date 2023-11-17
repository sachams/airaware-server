import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base
from server.types import Classification, Series, SiteStatus, Source


class SiteModel(Base):
    __tablename__ = "site"

    # Mandatory fields
    site_id: Mapped[int] = mapped_column(primary_key=True)
    site_code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    status: Mapped[SiteStatus]
    latitude: Mapped[float]
    longitude: Mapped[float]
    site_type: Mapped[Classification]
    source: Mapped[Source]

    # Optional fields
    photo_url: Mapped[str | None]
    description: Mapped[str | None]
    start_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    borough: Mapped[str | None]
