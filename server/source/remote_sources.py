import datetime

import app_config

from server.schemas import SensorDataSchema, SiteSchema
from server.source.breathe_london import BreatheLondon
from server.types import Series, Source


class RemoteSources:
    def __init__(self):
        self.sources = {Source.breathe_london: BreatheLondon(app_config.breathe_london_api_key)}

    def get_source(self, source: Source):
        """Returns the specified source or raises an exception if it doesn't exist"""
        if self.sources.get(source) is None:
            # TODO: best exception to raise?
            raise Exception("Not found")

        return self.sources[source]
