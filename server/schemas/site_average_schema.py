from pydantic import BaseModel, ConfigDict


class SiteAverageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_code: str
    value: float
