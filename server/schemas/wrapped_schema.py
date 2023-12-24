from pydantic import BaseModel, ConfigDict

from server.schemas.breach_schema import BreachSchema
from server.schemas.heatmap_schema import HeatmapSchema
from server.schemas.rank_schema import RankSchema
from server.schemas.site_schema import SiteSchema


class WrappedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    details: SiteSchema
    heatmap: dict[str, list[HeatmapSchema]]
    breach: dict[str, BreachSchema]
    rank: dict[str, RankSchema]
