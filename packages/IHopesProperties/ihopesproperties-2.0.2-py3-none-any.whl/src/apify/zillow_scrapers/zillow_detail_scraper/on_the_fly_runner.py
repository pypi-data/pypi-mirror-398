from typing import Optional

from apify.zillow_scrapers.zillow_detail_scraper.scraper import scrape_zillow_with_retry
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.property_contact_info import ListingContactInfo
from properties_defs.property_address import PropertyAddress


def generate_for_sale_property_from_address(address: str) -> Optional[ForSaleProperty]:
    """
    Generate a ForSaleProperty object from the address.
    :param address:
    :return:
    """

    property_data: Optional[dict] = scrape_zillow_with_retry(PropertyAddress.from_full_address(address))
    if not property_data:
        return None
    address_dict: dict = property_data['address']
    property_address: PropertyAddress = PropertyAddress(
        address=address_dict['streetAddress'],
        city=address_dict['city'],
        state=address_dict['state'],
        zip_code=address_dict['zipcode']
    )

    return ForSaleProperty(
        address=property_address,
        beds=property_data['bedrooms'],
        baths=property_data['bathrooms'],
        lat=property_data['latitude'],
        long=property_data['longitude'],
        sqft=property_data['livingArea'],
        lot_sqft=property_data['lotSize'],
        year_built=property_data['yearBuilt'],
        asking_price=property_data['price'],
        rentcast_pid="NA",
        listing_type="NA",
        listed_date="NA",
        days_on_market=0,
        last_event_date=property_data['priceHistory'][0]['date'],
        listing_agent=ListingContactInfo(
            name=property_data['attributionInfo']['agentName'],
            phone=property_data['attributionInfo']['agentPhoneNumber'],
            email=property_data['attributionInfo']['agentEmail']
        ),
        listing_office=ListingContactInfo(
            name=property_data['attributionInfo']['brokerName'],
            phone=property_data['attributionInfo']['brokerPhoneNumber']
        ),
        custom_fields=property_data
    )
