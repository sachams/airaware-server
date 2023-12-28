import functools
import json
import logging
import os

from server.repository.abstract_geometry_repository import AbstractGeometryRepository


@functools.cache
class GeometryRepository(AbstractGeometryRepository):
    """A repository that returns named geojson geometries. Note that we need to cache
    both the function call as well as the class to actually achieve caching"""

    @functools.cache
    def get_geometry(self, name: str) -> str:
        """Returns the named geometry, or None if it doesn't exist"""
        logging.info(f"Loading geometry {name} from file and caching result")
        path = f"geometry/{name}.json"

        if not os.path.exists(path):
            return None

        with open(path, "r") as geometry_file:
            geometry = json.load(geometry_file)
            return geometry
