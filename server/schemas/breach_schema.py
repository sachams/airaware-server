from pydantic import BaseModel, ConfigDict


class BreachSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ok: int
    breach: int
    no_data: int
