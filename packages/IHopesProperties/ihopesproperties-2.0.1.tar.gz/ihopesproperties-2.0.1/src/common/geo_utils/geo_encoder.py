from typing import Optional

import requests
import random

from common.addresses_utils.city_normalizer import normalize_city_name
from comps_extractor.utils.coordinates import AddressCoordinates
from properties_defs.property_address import PropertyAddress

from geopy.geocoders import Nominatim


def wrap_geocode(address: str):
    geolocator = Nominatim(
        user_agent=random.choice(["25to40", "IHopes", "IHopesProperties", "25to40IHopesProperties"]))
    location = geolocator.geocode(address, timeout=120)
    return location


def get_coordinates(property_address: PropertyAddress) -> Optional[AddressCoordinates]:
    coordinates: Optional[AddressCoordinates] = None

    # Try with as-is address
    address = f"{property_address.address}, {property_address.city}, {property_address.state}"
    location = wrap_geocode(address)
    if location:
        print(f'Found coordinates based on {address}')
        coordinates: AddressCoordinates = AddressCoordinates(
            address=property_address.get_full_address(),
            lat=location.latitude,
            lon=location.longitude
        )
    else:
        # Try with nornalized city (e.g.
        city = normalize_city_name(property_address.city)
        address = f"{property_address.address}, {city}, {property_address.state}"
        location = wrap_geocode(address)
        if location:
            coordinates: AddressCoordinates = AddressCoordinates(
                address=property_address.get_full_address(),
                lat=location.latitude,
                lon=location.longitude
            )
        else:
            # Try without city at all (e.g.
            address = f"{property_address.address}, {property_address.state}"
            location = wrap_geocode(address)
            if location:
                coordinates: AddressCoordinates = AddressCoordinates(
                    address=property_address.get_full_address(),
                    lat=location.latitude,
                    lon=location.longitude
                )
    if coordinates:
        print(f'Found location using {address}')
        return coordinates

    return None


def get_coordinates_deprecated(address: PropertyAddress) -> Optional[AddressCoordinates]:
    """
    Use the Nominatim API to get the latitude and longitude of an address.
    Consider add sleep time to avoid rate limiting.
    :param address: without zip code, e.g. "152 W Patty Ln, Monroeville, PA"
    :return: latitude and longitude
    """
    base_url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": random.choice(["25to40", "IHopes", "IHopesProperties", "25to40IHopesProperties"])
    }

    params = {
        "street": address.address,
        "city": address.city,
        "state": address.state,
        "country": "USA",
        "format": "json",
    }

    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    if data:
        location = data[0]
        latitude: float = float(location["lat"])
        longtitude: float = float(location["lon"])
        print(f"Coordinates for {address}: Latitude={latitude}, Longitude={longtitude}")

        return AddressCoordinates(
            address=address.get_full_address(),
            lat=latitude,
            lon=longtitude
        )
    else:
        print(f"No coordinates found for {address}")
        return None
