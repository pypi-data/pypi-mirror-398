from __future__ import annotations

from typing import Optional, Dict, Any

from apify.skip_trace.owner_data import PropertyOwnerInfo
from apify.zillow_scrapers.common.contingency_status_extractor import \
    transform_property_data_to_contingency_status
from flows.common.contingent_status import ContingentStatus
from properties_defs.properties.property import Property
from properties_defs.property_address import PropertyAddress
from properties_defs.property_contact_info import ListingContactInfo


class ForSaleProperty(Property):
    def __init__(self, rentcast_pid: str, address: PropertyAddress, beds: float, baths: float,
                 sqft: int, lot_sqft: float, lat: float, long: float, year_built: int, asking_price: int,
                 listing_type: str, listed_date: str, days_on_market: int, last_event_date: str,
                 last_listing_price: Optional[str] = None, listing_agent: Optional[ListingContactInfo] = None,
                 listing_office: Optional[ListingContactInfo] = None, custom_fields: Optional[Dict[Any, Any]] = None,
                 owner_info: Optional[PropertyOwnerInfo] = None):
        super().__init__(
            address=address,
            beds=beds,
            baths=baths,
            sqft=sqft,
            lot_sqft=lot_sqft,
            year_built=year_built,
            lat=lat,
            long=long,
        )
        self.rentcast_pid: str = rentcast_pid
        self.asking_price: int = asking_price
        self.listing_type: str = listing_type
        self.listed_date: str = listed_date
        self.days_on_market: int = days_on_market
        self.last_event_date: str = last_event_date
        self.last_listing_price: str = last_listing_price
        self.listing_agent: Optional[ListingContactInfo] = listing_agent
        self.listing_office: Optional[ListingContactInfo] = listing_office
        self.custom_fields: Optional[Dict[Any, Any]] = custom_fields
        self.owner_info: Optional[PropertyOwnerInfo] = owner_info

    def get_contingency_status(self) -> ContingentStatus:
        return transform_property_data_to_contingency_status(property_data=self.custom_fields)

    def __eq__(self, other: ForSaleProperty):
        return self.address.get_full_address() == other.address.get_full_address()

    def __hash__(self):
        return hash(self.address.get_full_address())
