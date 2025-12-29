
class AddressCoordinates:
    def __init__(self, address: str, lat: float, lon: float):
        self.address = address
        self.lat = lat
        self.long = lon

class BoundingBox:
    def __init__(self, max_lat: float, max_lon: float, min_lat: float, min_lon: float):
        self.max_lat = max_lat
        self.max_lon = max_lon
        self.min_lat = min_lat
        self.min_lon = min_lon
