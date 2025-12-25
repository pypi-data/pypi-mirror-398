from typing import List, Type

from apify.zillow_scrapers.common.contingency_status_extractor import get_contingency_status_by_address
from flows.common.contingent_status import ContingentStatus
from flows.leads_cleaner_flow.contingent_status_handlers import ContingentStatusMapper, AbstractContingentHandler
from flows.leads_cleaner_flow.get_leads_properties import get_leads_properties
from flows.leads_cleaner_flow.leads_task import LeadsTask


def run_leads_cleaner():
    """
    Run the leads cleaner flow, will update all the leads that are not active anymore.
    """
    print('Running leads cleaner flow')
    leads_properties: List[LeadsTask] = get_leads_properties()

    for leads_property in leads_properties:
        try:
            property_address: str = leads_property.address.get_full_address()
            print(f'\nLeads property: {property_address}')

            status: ContingentStatus = get_contingency_status_by_address(property_address=leads_property.address)
            print(f'For property {property_address}, status is {status.value}')

            handler_class: Type[AbstractContingentHandler] = ContingentStatusMapper().get_handler(status)
            handler_instance: AbstractContingentHandler = handler_class(leads_property)
            handler_instance.handle()
            print(f'Finished handling property: {property_address}')
        except Exception as e:
            print(f'Failed to process a property [error={e}]')
            continue


if __name__ == '__main__':
    run_leads_cleaner()