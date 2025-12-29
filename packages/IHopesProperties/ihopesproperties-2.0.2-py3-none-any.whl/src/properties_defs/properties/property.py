from __future__ import annotations
from typing import Optional

from properties_defs.property_address import PropertyAddress
from zillow.property_getter import construct_zillow_basic_property_url


class Property:
    def __init__(self, address: PropertyAddress, beds: float, baths: float, sqft: int, lot_sqft: float,
                 lat: float, long: float, year_built: Optional[int] = None, zillow_link: Optional[str] = None):
        self.address: PropertyAddress = address
        self.bedrooms: float = beds
        self.bathrooms: float = baths
        self.sqft: int = sqft
        self.lot_sqft: float = lot_sqft
        self.lat: float = lat
        self.long: float = long
        self.year_built: Optional[int] = year_built
        self.zillow_link: str = zillow_link if zillow_link \
            else construct_zillow_basic_property_url(self.address.get_full_address())

    def get_min_bedrooms(self):
        """
        Allow 1 less bedroom
        """
        return self.bedrooms - 1

    def get_max_bedrooms(self):
        """
        Allow 1 mor bedroom
        """
        return self.bedrooms + 1


    def get_min_sqft(self):
        """
        Consider up to 20% less than sqft
        :return:
        """
        return self.sqft * 0.8

    def get_max_sqft(self):
        """
        Consider up to 20% more than sqft
        :return:
        """
        return self.sqft * 1.2

    @staticmethod
    def sort_by_sold_date(properties: list) -> list:
        """
        Sort a list of Property objects by the sold date.
        :param properties: List of Property objects to sort.
        :return: Sorted list of Property objects.
        """
        from datetime import datetime

        def get_date_attr(prop):
            date_str = prop.sold_date
            return datetime.strptime(date_str, "%d-%m-%Y")

        return sorted(properties, key=get_date_attr, reverse=True)
