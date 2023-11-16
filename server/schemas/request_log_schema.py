import datetime

from pydantic import BaseModel, ConfigDict


class RequestLogBaseSchema(BaseModel):
    time: datetime.datetime
    ip_address: str
    path: str


class RequestLogSchema(RequestLogBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    request_id: int
