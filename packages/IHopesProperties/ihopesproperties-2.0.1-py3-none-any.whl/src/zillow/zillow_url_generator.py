import json
from enum import Enum
from urllib.parse import quote

from comps_extractor.utils.coordinates import BoundingBox
from properties_defs.properties.property import Property


class ListingStatus(Enum):
    SOLD = "sold"
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"


def generate_bonding_box_based_zillow_url(for_sale_property: Property, bounding_box: BoundingBox,
                                          sold_in_last_months: int = 6, status: ListingStatus = ListingStatus.SOLD)\
        -> str:
    """
    Generate a Zillow search URL dynamically with filters for sold properties.
    :param status:
    :param for_sale_property:
    :param state: State abbreviation (e.g., "pa").
    :param bounding_box: BoundingBox object containing min/max lat/lon.
    :param region_id: Zillow region ID.
    :param zoom: Map zoom level (default: 17).
    :param sold_in_last_months: Filter for properties sold within the last X months (default: 6).
    :return: Zillow search URL as a string.
    """
    # Base URL
    base_url = (f"https://www.zillow.com/"
                f"{quote(for_sale_property.address.city)}-{for_sale_property.address.state}/{status.value}/")

    # Filter for sold properties in the last X months
    date_range_filter = {
        1: "30",
        3: "90",
        6: "6m",
        12: "12m",
        24: "24m",
    }.get(sold_in_last_months, "6m")  # Default to "6m"

    # Build filterState
    filter_state = {
        "sort": {
            "value": "globalrelevanceex"
        },
        "fsba": {
            "value": False
        },
        "fsbo": {
            "value": False
        },
        "nc": {
            "value": False
        },
        "cmsn": {
            "value": False
        },
        "auc": {
            "value": False
        },
        "fore": {
            "value": False
        },
        "rs": {
            "value": True
        },
        "doz": {
            "value": date_range_filter
        },
        "beds": {
            "min": for_sale_property.get_min_bedrooms(),
            "max": for_sale_property.get_max_bedrooms()
        },
    }

    if for_sale_property.sqft:
        filter_state["sqft"] = {
            "min": for_sale_property.get_min_sqft(),
            "max": for_sale_property.get_max_sqft()
        }

    # Add property related filters

    # Build the searchQueryState JSON object
    search_query_state = {
        "pagination": {},
        "isMapVisible": True,
        "mapBounds": {
            "west": bounding_box.min_lon,
            "east": bounding_box.max_lon,
            "south": bounding_box.min_lat,
            "north": bounding_box.max_lat,
        },
        # "regionSelection": [
        #     {
        #         "regionId": for_sale_property.address.zip_code,
        #         "regionType": 7
        #     }
        # ],
        "filterState": filter_state,
        "isListVisible": True,
        "usersSearchTerm": f"{for_sale_property.address.city} {for_sale_property.address.state}".title(),
    }

    # Encode the JSON object as a URL-safe string
    search_query_state_encoded = quote(json.dumps(search_query_state))

    # Construct the full URL
    full_url = f"{base_url}?searchQueryState={search_query_state_encoded}"
    print(f'For the property {for_sale_property.address.get_full_address()}, the Zillow URL for its comps is: {full_url}')

    return full_url
