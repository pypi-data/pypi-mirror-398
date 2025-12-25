from typing import List, Optional

from comps_extractor.utils.bounding_box_calculator import calculate_bounding_box
from comps_extractor.utils.coordinates import AddressCoordinates, BoundingBox
from common.geo_utils.geo_encoder import get_coordinates
from apify.zillow_scrapers.zillow_search_scraper.scraper import scrape_zillow
from zillow.zillow_url_generator import generate_bonding_box_based_zillow_url
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty


def generate_comps(for_sale_property: ForSaleProperty, radius: Optional[float] = 0.5,
                   sold_in_last_months: Optional[int] = 6, test_mode: bool = False) -> List[SoldProperty]:
    """
    Generate comps for a for-sale property.
    :param for_sale_property: The for-sale property for which to find comps.
    :param radius: Radius in miles to search for comps.
    :param sold_in_last_months: Sold properties in the last N months.
    :param test_mode: Test mode flag.
    :return:
    """

    # Step 1: Get coordinates for the address
    if not for_sale_property.lat or not for_sale_property.long:
        address_coordinates: Optional[AddressCoordinates] = get_coordinates(for_sale_property.address)
        if not address_coordinates:
            print(f"Failed to get coordinates for address: {for_sale_property.address.get_full_address()}")
            return []
        for_sale_property.lat = address_coordinates.lat
        for_sale_property.long = address_coordinates.long
        print(f"Got coordinates successfully.")

    # Step 2: Calculate bounding box
    bounding_box: BoundingBox = calculate_bounding_box(
        lat=for_sale_property.lat,
        lon=for_sale_property.long,
        radius=radius
    )
    print(f"Created Bounding box successfully.")

    # Step 3: Construct Zillow URL with bounding box
    zillow_url = generate_bonding_box_based_zillow_url(
        for_sale_property=for_sale_property,
        bounding_box=bounding_box,
        sold_in_last_months=sold_in_last_months
    )
    print("Generated Zillow URL:", zillow_url)

    # Step 4: Scrape Zillow for comps
    scraped_properties: List[SoldProperty] = scrape_zillow(
        lead_property=for_sale_property,
        zillow_url=zillow_url,
        test_mode=test_mode
    )

    # Step 5: Sort scraped properties by sold date (most recent first)
    sorted_properties: List[SoldProperty] = SoldProperty.sort_by_sold_date(
        properties=scraped_properties
    )

    # We might have a scenario where the for-sale property is also in the comps list (if sold in the last 6 months),
    # hence removing it
    final_scraped_properties: List[SoldProperty] = \
        [prop for prop in sorted_properties
         if prop.address.get_full_address() != for_sale_property.address.get_full_address()]

    return final_scraped_properties
