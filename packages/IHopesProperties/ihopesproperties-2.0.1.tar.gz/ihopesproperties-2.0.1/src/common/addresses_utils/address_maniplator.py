import copy
from typing import List

from common.addresses_utils.city_normalizer import normalize_city_name
from common.utils.logger import log
from properties_defs.property_address import PropertyAddress


def update_address_with_pittsburgh_ciy(address: PropertyAddress) -> PropertyAddress:
    """
    We might have cases where the property's address is written with a city such as Baden or Penn Hills in some places
     while in others it is listed with Pittsburgh as city.
    This usually can happen as the task is originally created using Rentcast API which will fetch the address as
     city=Baldwin, although in Zillow it will appear with City=Pittsburgh.
     Also, it might appear with city=Baldwin even in Redfin.
    :param address: Original address
    :return: Updated address with city set to Pittsburgh
    """
    log(msg=f"Got address: {address.get_full_address()}", app_log=False)
    address_copy: PropertyAddress = copy.deepcopy(address)
    address_copy.city = 'Pittsburgh'
    log(msg=f"Updated address: {address_copy.get_full_address()}", app_log=False)
    return address_copy


def update_address_with_normalized_city(address: PropertyAddress) -> PropertyAddress:
    log(msg=f"Got address: {address.get_full_address()}", app_log=False)
    address_copy: PropertyAddress = copy.deepcopy(address)
    address_copy.city = normalize_city_name(city=address.city)
    log(msg=f"Updated address: {address_copy.get_full_address()}", app_log=False)
    return address_copy

def update_address_with_zillow_abbreviation(address: PropertyAddress):
    log(msg=f"Got address: {address.get_full_address()}", app_log=False)
    address_copy: PropertyAddress = copy.deepcopy(address)

    suffix_map = {
        "Road": "Rd",
        "Street": "St",
        "Avenue": "Ave",
        "Boulevard": "Blvd",
        "Drive": "Dr",
        "Court": "Ct",
        "Lane": "Ln",
        "Place": "Pl",
        "Terrace": "Ter",
        "Circle": "Cir",
    }

    parts = address_copy.address.title().split()
    if parts[-1] in suffix_map:
        parts[-1] = suffix_map[parts[-1]]

    address_copy.address = " ".join(parts)
    log(msg=f"Updated address: {address_copy.get_full_address()}", app_log=False)

    return address_copy


def get_all_possible_addresses(address: PropertyAddress) -> List[PropertyAddress]:
    """
    Generate all possible addresses, they might be identical hence wrapping with set to deduplicate.
    """
    return list({
        address,
        update_address_with_pittsburgh_ciy(address),
        update_address_with_normalized_city(address),
        update_address_with_zillow_abbreviation(address),
        address.get_address_without_zip_code(),
        update_address_with_pittsburgh_ciy(address).get_address_without_zip_code()
    })
