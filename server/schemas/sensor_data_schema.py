import datetime

from pydantic import BaseModel, ConfigDict

from server.types import Series


class SensorDataBaseSchema(BaseModel):
    time: datetime.datetime
    value: float


class SensorDataRemoteSchema(SensorDataBaseSchema):
    """This schema is returned from remote data sources"""

    pass


class SensorDataCreateSchema(SensorDataBaseSchema):
    site_id: int
    series: Series


class SensorDataSchema(SensorDataBaseSchema):
    model_config = ConfigDict(from_attributes=True)
