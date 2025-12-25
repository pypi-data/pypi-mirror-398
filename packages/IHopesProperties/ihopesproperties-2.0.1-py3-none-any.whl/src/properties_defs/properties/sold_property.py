from __future__ import annotations

from properties_defs.properties.property import Property
from properties_defs.property_address import PropertyAddress


class SoldProperty(Property):
    def __init__(self, zillow_pid: str, address: PropertyAddress, beds: float, baths: float,
                 sqft: int, lot_sqft: float, lat: float, long: float, dist_from_lead: float, zillow_link: str,
                 sold_price: int, sold_date: str):
        super().__init__(
            address=address,
            beds=beds,
            baths=baths,
            sqft=sqft,
            lot_sqft=lot_sqft,
            lat=lat,
            long=long,
            zillow_link=zillow_link
        )
        self.dist_from_lead: float = dist_from_lead
        self.zillow_pid: str = zillow_pid
        self.sold_price: int = sold_price
        self.sold_date: str = sold_date
