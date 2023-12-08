import app_config

from server.source.breathe_london import BreatheLondon
from server.types import Source


class RemoteSources:
    """Manages a set of remote sources, keyed by Source"""

    def __init__(self):
        self.sources = {Source.breathe_london: BreatheLondon(app_config.breathe_london_api_key)}

    def get_source(self, source: Source):
        """Returns the specified source or raises an exception if it doesn't exist"""
        if self.sources.get(source) is None:
            # TODO: best exception to raise?
            raise Exception("Not found")

        return self.sources[source]
