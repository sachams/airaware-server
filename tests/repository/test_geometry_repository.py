from server.repository.geometry_repository import GeometryRepository


def test_get():
    geo_repo = GeometryRepository()

    # Check we get something back
    geojson = geo_repo.get_geometry("ltns")
    assert geojson is not None
    assert len(geojson["features"]) > 0

    # It's cached, so check nothing funny happens when we call it again
    geojson = geo_repo.get_geometry("ltns")
    assert geojson is not None
    assert len(geojson["features"]) > 0

    # Now check that creating a new instance of the class is also cached

    geo_repo = GeometryRepository()

    # Check we get something back
    geojson = geo_repo.get_geometry("ltns")
    assert geojson is not None
    assert len(geojson["features"]) > 0
