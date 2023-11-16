import datetime

from pydantic import BaseModel, ConfigDict

from server.types import Series


class SensorDataBaseSchema(BaseModel):
    time: datetime.datetime
    value: float


class SensorDataCreateSchema(SensorDataBaseSchema):
    site_id: int
    series: Series
    pass


class SensorDataSchema(SensorDataBaseSchema):
    model_config = ConfigDict(from_attributes=True)
