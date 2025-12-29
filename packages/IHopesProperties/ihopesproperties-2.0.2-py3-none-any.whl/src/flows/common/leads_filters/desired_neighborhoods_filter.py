from typing import List

from flows.common.leads_filters.abstract_filter import LeadsFilter
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.property_address import PropertyAddress

BEECHVIEW = ["15216"]
BROOKLINE = ["15226"]
MOUNT_WASHINGTON = ["15211"]
AVALON = ["15212"]
BELLEVUE = ["15202"]
BEN_AVON = ["15202"]
EMSWORTH = ["15202"]
BRIGHTON_HEIGHTS = ["15202", "15212"]
GREENFIELD = ["15207", "15217"]
BLOOMFIELD = ["15224"]
SQUIRREL_HILL = ["15217"]
CASTLE_SHANNON = ["15234"]
DORMONT = ["15216"]
BRENTWOOD = ["15227"]
MT_LEBANON = ["15228"]
MT_WASHINGTON = ["15211"]
GREEN_TREE = ["15242", "15220", "15205"]
SWISSVALE = ["15218", "15120"]
PLUM_BORO = ["15239"]
SOITH_SIDE = ["15203"]


class DesiredNeighborhoodsFilter(LeadsFilter):
    """
    White list of inside & outside Pittsburgh neighborhoods
    """

    def __init__(self, in_city_zip_codes: List[List[int]], out_city_neighborhoods: List[str]):
        super().__init__('In City Neighborhoods Filter')
        # Flatten the list of lists
        self.in_city_zip_codes: List[int] = [zip_code for zip_codes in in_city_zip_codes for zip_code in zip_codes]
        self.normalized_out_city_neighborhoods = {n.lower() for n in out_city_neighborhoods}

    def valid_inside_city(self, property_address: PropertyAddress) -> bool:
        city = property_address.city.strip().lower()
        in_pittsburgh: bool = city == 'pittsburgh'
        in_city_zip_code_valid: bool = property_address.zip_code in self.in_city_zip_codes

        return in_pittsburgh and in_city_zip_code_valid

    def valid_outside_city(self, property_address: PropertyAddress) -> bool:
        city = property_address.city.strip().lower()
        in_pittsburgh: bool = city == 'pittsburgh'
        out_city_neighborhood_valid: bool = city in self.normalized_out_city_neighborhoods

        return not in_pittsburgh and out_city_neighborhood_valid

    def is_in_desired_neighborhood(self, property_address: PropertyAddress) -> bool:
        """
        Determines if a property is located in a desired neighborhood.

        A property is considered desirable if:
        - It is located in the city of Pittsburgh and in one of the allowed zip codes; OR
        - It is outside of Pittsburgh but in an approved nearby neighborhood.

        :param lead: A ForSaleProperty object containing address details.
        :return: True if the property is in a desired neighborhood, False otherwise.
        """
        return self.valid_inside_city(property_address) or self.valid_outside_city(property_address)

    def apply_filter(self, leads: List[ForSaleProperty]) -> List[ForSaleProperty]:
        """
        Apply is_in_desired_neighborhood filter of the given for sale properties leads
        """
        in_city_leads: List[ForSaleProperty] = \
            [lead for lead in leads if self.is_in_desired_neighborhood(lead.address)]

        return in_city_leads


DESIRED_NEIGHBORHOODS_FILTER: DesiredNeighborhoodsFilter = DesiredNeighborhoodsFilter(
    in_city_zip_codes=[
        BEECHVIEW,
        BROOKLINE,
        MOUNT_WASHINGTON,
        BRIGHTON_HEIGHTS,
        GREENFIELD,
        BLOOMFIELD,
        SQUIRREL_HILL,
        CASTLE_SHANNON,
        DORMONT,
        BRENTWOOD,
        MT_LEBANON,
        MT_WASHINGTON,
        GREEN_TREE,
        SWISSVALE,
        PLUM_BORO,
        SOITH_SIDE,
        AVALON,
        BELLEVUE,
        BEN_AVON,
        EMSWORTH,
    ],
    out_city_neighborhoods=[
        "Monroeville", "Dormont", "Castle Shannon", "Whitehall", "Brentwood",
        "Baldwin", "Baldwin Boro", "Brookline", "MT Lebanon", "Mt. Lebanon", "Carnegie", "Scott Township",
        "MT Washington", "Bethel Park", "Greentree", "Crafton", "Avalon", "Bellevue",
        "Swissvale", "Beaver Falls", "Lawrenceville", "Overbrook", "Brighton Heights",
        "Beechview", "Brookline", "Greenfield", "Bloomfield", "Squirrel Hill", "Castle Shannon",
        "Green Tree", "Plum Boro", "Munhall",
        # New neighborhoods
        "Bridgeville", "Banksville", "Westwood", "Banksville/Westwood", "Mars Boro", "Emsworth", "Jefferson Hills",
        "West View", "Cheswick", "Leetsdale", "Ross Twp", "Ross Township", "Cranberry Township", "Cranberry Twp",
        "South Side", "Shaler", "Cecil"

        #Sharpsburgh, etna, Millvale
    ]
)
