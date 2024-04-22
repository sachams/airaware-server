from pydantic import BaseModel, ConfigDict

from server.schemas.site_schema import SiteSchema


class SiteAverageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_code: str
    value: float
    site_details: SiteSchema | None = None
