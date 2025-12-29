import os, pickle
from functools import lru_cache
from typing import Optional

import geopandas as gpd
from shapely.geometry import Point

from comps_extractor.utils.coordinates import AddressCoordinates
from common.geo_utils.geo_encoder import get_coordinates
from properties_defs.property_address import PropertyAddress


@lru_cache(maxsize=1)
def get_zip_shapes():
    # Load ZCTA (ZIP Code Tabulation Areas) shapefile

    # Read it once and saved as pickle
    # zip_shapes = gpd.read_file("cb_2020_us_zcta520_500k.zip")
    # zip_shapes = zip_shapes.to_crs("EPSG:4326")  # ensure lat/lon
    # with open('geo_zips.pickle', 'wb') as token:
    #     pickle.dump(zip_shapes, token)

    script_dir = os.path.dirname(__file__)  # directory where the script is
    file_path = os.path.join(script_dir, "geo_zips.pickle")

    with open(file_path, 'rb') as token:
        zip_shapes = pickle.load(token)

    return zip_shapes


def find_zip_code(property_address: PropertyAddress) -> Optional[str]:
    """
    Given latitude and longitude of a property, return the ZIP code
    from the Census ZCTA shapefile.
    """

    address_coordinates: Optional[AddressCoordinates] = get_coordinates(property_address)
    if not address_coordinates:
        print(f'Can not find lat/long coordinates for {property_address.get_full_address()}')
        return None

    point = Point(address_coordinates.long, address_coordinates.lat)  # note: order is (lon, lat)
    zip_shapes = get_zip_shapes()
    match = zip_shapes[zip_shapes.contains(point)]
    if not match.empty:
        return match.iloc[0]["ZCTA5CE20"]
    print(f'Can not find zip code for {address_coordinates}')
    return None
