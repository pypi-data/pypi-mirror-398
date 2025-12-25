from typing import List

import requests

from flows.leads_generator_flow.flow.lead_source import LeadQuerySource
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.property_contact_info import ListingContactInfo
from properties_defs.property_address import PropertyAddress

API_KEY = "b632a2d8212f4bb0bb88fc43dd6b976f"
BASE_URL = "https://api.rentcast.io/v1"

def fetch_active_for_sale_properties(lead_source: LeadQuerySource, test_mode: bool = False) -> List[ForSaleProperty]:
    """
    Fetch listings from RentCast API.
    """

    if test_mode:
        import pickle
        with open('for_sale_properties_test_data.pickle', 'rb') as token:
            return pickle.load(token)

    endpoint = f"{BASE_URL}/listings/sale"

    headers = {
        "accept": "application/json",
        "X-Api-Key": API_KEY
    }

    limit: int = 500
    params = {
        #"latitude": downtown_pittsburgh_latitude,
        #"longitude": downtown_pittsburgh_longitude,
        #"radius": radius,
        "city": lead_source.city,
        "state": lead_source.state,
        "propertyType": 'Single Family',
        "status": 'Active',
        "limit": limit
    }

    if lead_source.zipcode:
        params["zipCode"] = lead_source.zipcode

    # Iterate as long as there are more results
    offset = 0
    for_sale_properties: List[ForSaleProperty] = []
    while True:
        curr_offset_properties: List[ForSaleProperty] = pagination_request(endpoint, headers, params, offset)
        for_sale_properties.extend(curr_offset_properties)

        if not curr_offset_properties:
            print(f"No properties found at all. Stopping the process.")
            break

        fetched_all_properties: bool = len(curr_offset_properties) < limit
        if fetched_all_properties:
            break

        offset += limit

    sorted_for_sale_properties: List[ForSaleProperty] = sort_for_sale_properties_by_listing_date(for_sale_properties)
    return sorted_for_sale_properties


def sort_for_sale_properties_by_listing_date(for_sale_properties: List[ForSaleProperty]) -> List[ForSaleProperty]:
    """
    Sort for sale property by their listing date.
    By that - we can iterate and stop when we reach the first property that we already have a task for.
    :param for_sale_properties:
    :return:
    """
    return sorted(for_sale_properties, key=lambda x: x.listed_date)


def pagination_request(endpoint: str, headers: dict, params: dict, offset: int) -> List[ForSaleProperty]:
    """
    Make a request to the RentCast API with pagination.
    :param endpoint:
    :param headers:
    :param params:
    :param offset:
    :return:
    """

    # API has a 20 requests per second limit, sleep accordingly
    import time
    time.sleep(0.05)  # 50 ms, 1/20 = 0.05

    params["offset"] = offset
    response = requests.get(endpoint, headers=headers, params=params)
    if response.status_code == 200:
        response_dicts: List[dict] = response.json()
        for_sale_properties: List[ForSaleProperty] = \
            [transform_response_to_property(response_dict) for response_dict in response_dicts]
        return for_sale_properties
    else:
        response.raise_for_status()


def transform_response_to_property(response_data_dict: dict) -> ForSaleProperty:
    """
    Transform the response data from the RentCast API into a ForSaleProperty.

    :param response_data_dict: The response data from the RentCast API.
    :return: A ForSaleProperty object.
    """

    def build_listing_agent() -> ListingContactInfo:
        listing_agent: Dict = response_data_dict.get('listingAgent')
        if not listing_agent:
            return ListingContactInfo()

        return ListingContactInfo(
            name=listing_agent['name'] if 'name' in listing_agent else None,
            phone=listing_agent['phone'] if 'phone' in listing_agent else None,
            email=listing_agent['email'] if 'email' in listing_agent else None
        )

    def build_listing_ofice() -> ListingContactInfo:
        listing_office: Dict = response_data_dict.get('listingOffice')
        if not listing_office:
            return ListingContactInfo()

        return ListingContactInfo(
            name=listing_office['name'] if 'name' in listing_office else None,
            phone=listing_office['phone'] if 'phone' in listing_office else None,
            email=listing_office['email'] if 'email' in listing_office else None
        )

    return ForSaleProperty(
        rentcast_pid=response_data_dict.get("id"),
        address=PropertyAddress.from_full_address(response_data_dict.get('formattedAddress')),
        beds=response_data_dict.get("bedrooms"),
        baths=response_data_dict.get("bathrooms"),
        sqft=response_data_dict.get("squareFootage"),
        lot_sqft=response_data_dict.get("lotSize"),
        lat=response_data_dict.get("latitude"),
        long=response_data_dict.get("longitude"),
        year_built=response_data_dict.get("yearBuilt"),
        asking_price = response_data_dict.get("price"),
        listing_type=response_data_dict.get("listingType"),
        listed_date=response_data_dict.get("listedDate")[:10],  # Keep only year-month-day
        days_on_market=response_data_dict.get("daysOnMarket"),
        last_event_date="NA",
        listing_agent=build_listing_agent(),
        listing_office=build_listing_ofice()
    )


