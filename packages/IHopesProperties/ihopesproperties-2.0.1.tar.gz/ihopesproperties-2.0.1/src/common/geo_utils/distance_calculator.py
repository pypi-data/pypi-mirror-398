def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface.

    Parameters:
    - lat1, lon1: Latitude and Longitude of point 1 in decimal degrees.
    - lat2, lon2: Latitude and Longitude of point 2 in decimal degrees.

    Returns:
    - Distance in miles.
    """
    # Earth radius in miles
    R = 3958.8

    # Convert latitude and longitude from degrees to radians
    import math
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Differences in latitude and longitude
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in miles
    distance = R * c
    return distance
