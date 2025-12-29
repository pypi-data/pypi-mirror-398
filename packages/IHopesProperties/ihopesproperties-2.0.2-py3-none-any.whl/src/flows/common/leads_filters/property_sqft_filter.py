from typing import List

from flows.common.leads_filters.abstract_filter import LeadsFilter
from properties_defs.properties.for_sale_property import ForSaleProperty


class SqftFilter(LeadsFilter):
    """
    Filter properties by number of bedrooms
    """

    def __init__(self, min_sqft: int):
        super().__init__('Sqft Filter')
        self.min_sqft: int = min_sqft

    def apply_filter(self, leads: List[ForSaleProperty]) -> List[ForSaleProperty]:
        return [lead for lead in leads if not lead.sqft or self.min_sqft <= lead.sqft]


SQFT_FILTER: SqftFilter = SqftFilter(
    min_sqft=800
)
