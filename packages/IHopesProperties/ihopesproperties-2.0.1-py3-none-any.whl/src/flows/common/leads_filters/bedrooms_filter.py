from typing import List

from flows.common.leads_filters.abstract_filter import LeadsFilter
from properties_defs.properties.for_sale_property import ForSaleProperty


class BedroomsFilter(LeadsFilter):
    """
    Filter properties by number of bedrooms
    """

    def __init__(self, min_bedrooms: int, max_bedrooms: int):
        super().__init__('Bedrooms Filter')
        self.min_bedrooms: int = min_bedrooms
        self.max_bedrooms: int = max_bedrooms

    def apply_filter(self, leads: List[ForSaleProperty]) -> List[ForSaleProperty]:
        return [lead for lead in leads if self.min_bedrooms <= lead.bedrooms <= self.max_bedrooms]


BEDROOMS_FILTER: BedroomsFilter = BedroomsFilter(
    min_bedrooms=2,
    max_bedrooms=4
)
