import datetime

from pydantic import BaseModel, ConfigDict

from server.types import Classification, SiteStatus, Source


class SiteBaseSchema(BaseModel):
    # Mandatory fields
    code: str
    name: str
    status: SiteStatus
    latitude: float
    longitude: float
    site_type: Classification
    source: Source

    # Optional fields
    photo_url: str | None
    description: str | None
    start_date: datetime.datetime | None
    end_date: datetime.datetime | None
    borough: str | None


class SiteCreateSchema(SiteBaseSchema):
    pass


class SiteSchema(SiteBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    site_id: int | None
