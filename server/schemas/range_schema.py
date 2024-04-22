import datetime

from pydantic import BaseModel


class RangeSchema(BaseModel):
    start: datetime.datetime
    end: datetime.datetime
