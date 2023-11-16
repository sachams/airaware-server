from enum import Enum


class Classification(str, Enum):
    unknown = "unknown"
    urban_background = "urban_background"
    suburban = "suburban"
    kerbside = "kerbside"
    industrial = "industrial"
    roadside = "roadside"
    rural = "rural"
