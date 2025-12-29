import math

from comps_extractor.utils.coordinates import BoundingBox


def calculate_bounding_box(lat: float, lon: float, radius: float = 0.5) -> BoundingBox:
    """
    Calculate the bounding box for a given latitude, longitude, and radius.

    :param lat: Latitude of the center point (degrees)
    :param lon: Longitude of the center point (degrees)
    :param radius: Radius around the center point (miles)
    :return: Tuple (min_lat, min_lon, max_lat, max_lon)
    """
    # Approximate degree changes per mile
    lat_change = radius / 69
    lon_change = radius / (69 * math.cos(math.radians(lat)))

    # Calculate bounding box
    min_lat = lat - lat_change
    max_lat = lat + lat_change
    min_lon = lon - lon_change
    max_lon = lon + lon_change

    print(f"Created Bounding box for {lat}, {lon} with radius {radius} miles")
    print(f"Bounding box: min_lat={min_lat}, min_lon={min_lon}, max_lat={max_lat}, max_lon={max_lon}")

    return BoundingBox(
        max_lat=max_lat,
        max_lon=max_lon,
        min_lat=min_lat,
        min_lon=min_lon
    )
