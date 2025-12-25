from typing import List, Optional

from apify.zillow_scrapers.common.client import MyApifyClient
from apify.zillow_scrapers.common.actor import Actor
from common.geo_utils.distance_calculator import calculate_distance
from properties_defs.properties.property import Property
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty
from properties_defs.property_address import PropertyAddress


def scrape_zillow(lead_property: ForSaleProperty, zillow_url: str, test_mode: bool = False) -> List[SoldProperty]:
    """
    Run the Apify Zillow scraper using the Apify client.

    :param lead_property: The for-sale property for which to find comps.
    :param zillow_url: The Zillow search URL to scrape.
    :return: Details of the scraper execution, including a link to the dataset.
    """
    # Initialize the Apify client
    apify_client: MyApifyClient = MyApifyClient(actor=Actor.ZILLOW_SEARCH_SCRAPER)

    # Prepare the Actor input
    run_input = {
        "searchUrls": [
            {
                "url": zillow_url
            }
        ],
    }

    # Fetch and print Actor results from the run's dataset (if there are any)
    scraped_properties: List[SoldProperty] = []
    raw_scraped_properties: Optional[List[dict]] = apify_client.run_client(run_input=run_input)
    if raw_scraped_properties:
        for item in raw_scraped_properties:
            print(item)
            scraped_properties.append(transform_response_to_property(
                lead_property=lead_property,
                response_data_dict=item
            ))

    return scraped_properties


def transform_response_to_property(lead_property: ForSaleProperty, response_data_dict: dict) -> SoldProperty:
    """
    Transform the response data from the Zillow scraper into a list of Property objects.

    :param response_data_dict: The response data from the Zillow scraper.
    :return: A list of Property objects.
    """

    return SoldProperty(
        address=PropertyAddress(
            address=response_data_dict.get("addressStreet"),
            city=response_data_dict.get("addressCity"),
            state=response_data_dict.get("addressState"),
            zip_code=response_data_dict.get("addressZipcode")
        ),
        zillow_pid=response_data_dict.get("zpid"),
        zillow_link=response_data_dict.get("detailUrl"),
        beds=response_data_dict.get("beds"),
        baths=response_data_dict.get("baths"),
        sqft=response_data_dict.get("area"),
        lot_sqft=response_data_dict.get("hdpData").get("homeInfo").get("lotAreaValue"),  # Convert acres to sqft
        lat=response_data_dict.get("latLong").get("latitude"),
        long=response_data_dict.get("latLong").get("longitude"),
        dist_from_lead=round(calculate_distance(
            lat1=lead_property.lat,
            lon1=lead_property.long,
            lat2=response_data_dict.get("latLong").get("latitude"),
            lon2=response_data_dict.get("latLong").get("longitude")
        ),2) if "latLong" in response_data_dict and "latitude" in response_data_dict.get("latLong")
                and "longitude" in response_data_dict.get("latLong")else "NA" ,
        sold_price=response_data_dict.get("unformattedPrice"),
        sold_date=get_sold_date(response_data_dict),
    )


def get_sold_date(response_data_dict):
    try:
        from datetime import datetime
        # Milliseconds timestamp
        millis = response_data_dict['hdpData']['homeInfo']['dateSold']  # Example: corresponds to '2023-01-01 00:00:00'
        # Convert milliseconds to seconds (datetime expects seconds)
        seconds = millis / 1000
        # Convert to a datetime object
        date = datetime.fromtimestamp(seconds)
        # Format as a readable string
        sold_date = date.strftime('%d-%m-%Y')
    except Exception as e:
        raise ValueError(f"Could not extract sold date from response data: {e}. "
                         f"We cannot extract comps without a sold date.")
    return sold_date
