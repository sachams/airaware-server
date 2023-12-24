from pydantic import BaseModel, ConfigDict


class RankSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rank: int
    value: float

