import json
import os

from server.repository.abstract_geometry_repository import AbstractGeometryRepository


class GeometryRepository(AbstractGeometryRepository):
    """A repository that returns named geojson geometries"""

    def get_geometry(self, name: str) -> str:
        """Returns the named geometry, or None if it doesn't exist"""
        path = f"geometry/{name}.json"

        if not os.path.exists(path):
            return None

        with open(path, "r") as geometry_file:
            geometry = json.load(geometry_file)
            return geometry
