import datetime

from pydantic import BaseModel, ConfigDict

from server.types import Classification, SiteStatus, Source


class SiteBaseSchema(BaseModel):
    # Mandatory fields
    site_code: str
    name: str
    status: SiteStatus
    latitude: float
    longitude: float
    site_type: Classification
    source: Source

    # Optional fields
    is_enabled: bool | None = None
    photo_url: str | None = None
    description: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    borough: str | None = None


class SiteCreateSchema(SiteBaseSchema):
    pass


class SiteSchema(SiteBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    site_id: int | None
