from collections import defaultdict

from pydantic import BaseModel

from server.schemas.range_schema import RangeSchema
from server.schemas.sensor_data_schema import SensorDataSchema


class OutlierBlockSchema(BaseModel):
    range: RangeSchema
    context_data: list[SensorDataSchema] = []
    outlier_data: dict[str, list[SensorDataSchema]] = defaultdict(list)
