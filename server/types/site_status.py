from enum import Enum


class SiteStatus(str, Enum):
    unknown = "unknown"
    healthy = "healthy"
    offline = "offline"
    coming_online = "coming_online"
    needs_attention = "needs_attention"
