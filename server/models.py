from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    site_code = Column(String, index=True)
    series = Column(String, index=True)
    time = Column(DateTime(timezone=True))
    value = Column(Float)
