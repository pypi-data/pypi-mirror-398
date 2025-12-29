from datetime import date
from typing import List, Type

from asana import TasksApi

from apify.zillow_scrapers.common.contingency_status_extractor import get_contingency_status
from flows.under_contract_follow_up_flow.contingent_status_handlers import ContingentStatus, ContingentStatusMapper, \
    AbstractContingentHandler
from flows.under_contract_follow_up_flow.get_under_contract_properties import get_under_contract_properties
from flows.under_contract_follow_up_flow.under_contract_task import UnderContractTask
from my_asana.authenticate import get_tasks_api


def run_under_contract_leads_flow():
    """
    Run the under contract follow-up flow, will update the under contract properties according to their status.
    :return:
    """
    print('Running under contract follow-up flow')
    under_contract_properties: List[UnderContractTask] = get_under_contract_properties()
    print(f'Found {len(under_contract_properties)} under contract properties')

    tasks_api: TasksApi = get_tasks_api()
    for under_contract_property in under_contract_properties:
        try:
            property_address: str = under_contract_property.address.get_full_address()
            print(f'Under contract property: {property_address}')

            status: ContingentStatus = get_contingency_status(under_contract_task=under_contract_property)
            print(f'For property {property_address}, status is {status.value}')

            # Update the due date to today
            today: str = date.today().strftime("%Y-%m-%d")
            tasks_api.update_task(
                task_gid=under_contract_property.gid,
                body={"data": {"due_on": today}},
                opts={}
            )

            handler_class: Type[AbstractContingentHandler] = ContingentStatusMapper().get_handler(status)
            handler_instance: AbstractContingentHandler = handler_class(under_contract_property)
            handler_instance.handle()
            print(f'Finished handling property: {property_address}')
        except Exception as e:
            print(f'Failed to process a property [error={e}]')
            continue


if __name__ == '__main__':
    run_under_contract_leads_flow()
