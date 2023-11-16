from pydantic import BaseModel


class SiteAverageSchema(BaseModel):
    site_code: str
    value: float
