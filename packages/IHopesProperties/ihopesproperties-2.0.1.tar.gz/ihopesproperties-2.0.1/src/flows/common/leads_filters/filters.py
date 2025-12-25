import copy
from typing import List

from common.utils.logger import log
from flows.common.leads_filters.abstract_filter import LeadsFilter
from flows.common.leads_filters.ap_filter import ASKING_PRICE_FILTER
from flows.common.leads_filters.bedrooms_filter import BEDROOMS_FILTER
from flows.common.leads_filters.desired_neighborhoods_filter import DESIRED_NEIGHBORHOODS_FILTER
from flows.common.leads_filters.property_sqft_filter import SQFT_FILTER
from properties_defs.properties.for_sale_property import ForSaleProperty

leads_filters: List[LeadsFilter] = [
    DESIRED_NEIGHBORHOODS_FILTER, # Has to be the first filter
    ASKING_PRICE_FILTER,
    BEDROOMS_FILTER,
    SQFT_FILTER
]


def apply_filters(for_sale_properties: List[ForSaleProperty], filters: List[LeadsFilter]) -> List[ForSaleProperty]:
    """
    Filter given for sale properties based on given filters. Return the final remaining valid leads.
    """
    log(msg=f'Starting to filter for sale properties, got total of {len(for_sale_properties)} properties '
            f'and {len(filters)} filters')

    filtered_properties: List[ForSaleProperty] = copy.deepcopy(for_sale_properties)
    for filter in filters:
        filtered_properties: List[ForSaleProperty] = filter.apply_filter(filtered_properties)
        log(msg=f'After applying filter {filter.name}, {len(filtered_properties)} properties left')
    log(msg=f'Finished filtering with total of {len(filtered_properties)} properties')
    return filtered_properties
