from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base
from server.types import SiteStatus


class BrokenSiteModel(Base):
    """Maintain a list of broken sites where we have to override the status"""

    __tablename__ = "broken_site"

    site_id: Mapped[int] = mapped_column(ForeignKey("site.site_id"), primary_key=True)
    status: Mapped[SiteStatus]
