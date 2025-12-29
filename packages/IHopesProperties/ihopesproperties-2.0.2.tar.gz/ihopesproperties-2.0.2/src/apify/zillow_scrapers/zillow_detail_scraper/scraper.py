from typing import List, Optional

from apify.zillow_scrapers.common.client import MyApifyClient
from apify.zillow_scrapers.common.actor import Actor
from common.addresses_utils.address_maniplator import get_all_possible_addresses
from properties_defs.property_address import PropertyAddress


def scrape_zillow_with_retry(address: PropertyAddress) -> Optional[dict]:
    """
    We will first try to scrape the data with the original city, and if it fails we have 2 possible addresses
     to fetch the data with:
    1. We might have different cities in the address, e.g. Baden vs. Pittsburgh. This can happen as the task is
    originally created using Rentcast API which will fetch the address as city=Baldwin,
    although in Zillow it will appear with City=Pittsburgh.
    2. Common in the expired listing flow, we might get from MLS (OneHome) addresses such as -
    293 Grandview Way, Charleroi Boro, PA 15022, while Zillow is familiar with
    293 Grandview Way, Charleroi, PA 15022 (without Boro), hence - trying with the normalized city approach.
    """
    ordered_possible_addresses: List[PropertyAddress] = get_all_possible_addresses(address)

    for possible_address in ordered_possible_addresses:
        property_data: dict = scrape_zillow(possible_address.get_full_address())
        if property_data['isValid']:
            return property_data
        else:
            print(f"Property data is not valid for: {possible_address.get_full_address()}")
    print(f"Can not get property data at all")
    return None


def scrape_zillow(address: str) -> dict:
    """
    Scrape the Zillow website using the Zillow Detail Scraper actor.
    :param address:
    :return:
    """
    # Initialize the Apify client
    apify_client: MyApifyClient = MyApifyClient(actor=Actor.ZILLOW_DETAIL_SCRAPER)

    # Prepare the Actor input
    run_input = {
        "addresses": [address]
    }

    # Fetch and print Actor results from the run's dataset (if there are any)
    items: list = apify_client.run_client(run_input=run_input)
    if len(items) > 1:
        raise ValueError(f"Expected only one item in the list, but got {len(items)} items.")

    property_data: dict = items[0]
    return property_data
