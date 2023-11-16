import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base
from server.types import Series


class SensorDataModel(Base):
    __tablename__ = "sensor_data"

    site_id: Mapped[int] = mapped_column(ForeignKey("site.site_id"), primary_key=True)
    series: Mapped[Series] = mapped_column(primary_key=True)
    time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    value: Mapped[float]
