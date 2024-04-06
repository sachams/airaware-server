import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base
from server.types import Classification, SiteStatus, Source


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
    is_data_ok: Mapped[bool] = mapped_column(default=True)

    # Optional fields
    is_enabled: Mapped[bool | None]
    photo_url: Mapped[str | None]
    description: Mapped[str | None]
    start_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    end_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    borough: Mapped[str | None]
