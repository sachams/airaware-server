import json

from shapely.geometry import Point, shape


class NotFoundError(Exception):
    pass


class BoroughMapper:
    """Maps lat/long positions into London boroughsm based on a
    borough geojson file"""

    def __init__(self, raise_if_not_found=False):
        with open("geometry/boroughs.json") as f:
            boundaries = json.load(f)

        self.polygons = {}
        self.raise_if_not_found = raise_if_not_found

        for feature in boundaries["features"]:
            polygon = shape(feature["geometry"])
            self.polygons[feature["properties"]["name"]] = polygon

    def get_borough(self, latitude, longitude):
        point = Point(longitude, latitude)

        for name, polygon in self.polygons.items():
            if polygon.contains(point):
                return name

        if self.raise_if_not_found:
            raise NotFoundError(f"Unable to find borough for point {point}")
        
        return "Outside London"
