from server.repository.abstract_geometry_repository import AbstractGeometryRepository


class FakeGeometryRepository(AbstractGeometryRepository):
    """A repository that returns named geojson geometries"""

    def get_geometry(self, name: str) -> str:
        """Returns the named geometry, or None if it doesn't exist"""
        if name == "exists":
            return {"ping": "pong"}

        return None
