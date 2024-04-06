from pydantic import BaseModel, ConfigDict

from server.types import Series


class SyncSiteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    site_code: str
    series: Series
