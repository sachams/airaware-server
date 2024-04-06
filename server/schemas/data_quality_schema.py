from pydantic import BaseModel, ConfigDict

from server.types import DataStatus, Series


class DataQualitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_code: str
    series: Series
    data_status: DataStatus
