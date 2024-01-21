from pydantic import BaseModel, ConfigDict, model_serializer


class HeatmapSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hour: int
    day: int
    value: float

    @model_serializer
    def ser_model(self) -> tuple:
        return (self.hour, self.day, round(self.value, 2))
