import pyproj

import shapely
from shapely.ops import transform
from shapely.geometry import shape


# "EPSG:4326", "EPSG:27700"
class ReprojGeojson:
    @staticmethod
    def transform(src_geojson, src, dest):
        project = pyproj.Transformer.from_proj(pyproj.Proj(src), pyproj.Proj(dest), always_xy=True)

        # Iterate over input features and transform
        dest_geojson = src_geojson.copy()

        # Remove any deprecated crs field
        if "crs" in dest_geojson:
            del dest_geojson["crs"]

        for feature in dest_geojson["features"]:
            # Extract actual geometry
            src_shape = shape(feature["geometry"])

            # Apply projection
            dest_shape = transform(project.transform, src_shape)

            # And save the new geomertry
            feature["geometry"] = shapely.geometry.mapping(dest_shape)

            # Also save the centroid of the area
            feature["properties"]["centre"] = shapely.geometry.mapping(dest_shape.centroid)

        return dest_geojson
