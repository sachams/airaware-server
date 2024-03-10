import datetime

from pydantic import BaseModel, ConfigDict, model_serializer

from server.schemas.sensor_data_schema import SensorDataSchema
from server.types import Series


class BadDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    series: Series
    site_code: str
    data: list[SensorDataSchema]
