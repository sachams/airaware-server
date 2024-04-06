from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base
from server.types import DataStatus, Series


class DataQualityModel(Base):
    __tablename__ = "data_quality"

    site_id: Mapped[int] = mapped_column(
        ForeignKey("site.site_id"), primary_key=True, index=True
    )
    series: Mapped[Series] = mapped_column(primary_key=True)
    data_status: Mapped[DataStatus] = mapped_column()
