from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    site_code = Column(String, index=True, primary_key=True, nullable=False)
    series = Column(String, index=True, primary_key=True, nullable=False)
    time = Column(DateTime(timezone=True), primary_key=True, index=True, nullable=False)
    value = Column(Float, nullable=False)
