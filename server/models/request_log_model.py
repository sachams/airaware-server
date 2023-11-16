import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class RequestLogModel(Base):
    __tablename__ = "request_log_new"

    request_id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str]
    path: Mapped[str]
