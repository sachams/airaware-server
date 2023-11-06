import datetime
from pydantic import BaseModel


class SensorDataBase(BaseModel):
    time: datetime.datetime
    value: float


class SensorDataCreate(SensorDataBase):
    pass


class SensorData(SensorDataBase):
    class Config:
        orm_mode = True


class SiteAverage(BaseModel):
    site_code: str
    value: float
