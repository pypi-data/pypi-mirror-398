from datetime import date
from typing import List, Dict

from asana import TasksApi

from flows.under_contract_follow_up_flow.under_contract_task import UnderContractTask
from my_asana.authenticate import get_tasks_api
from my_asana.consts import FOLLOW_UPS_UNDER_CONTRACT_SECTION


def get_today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def get_task_due_date(tasks_api: TasksApi, under_contract_task: UnderContractTask) -> str:
    return tasks_api.get_task(under_contract_task.gid, opts={})['due_on']


def get_under_contract_properties() -> List[UnderContractTask]:
    tasks_api: TasksApi = get_tasks_api()
    raw_tasks: List[Dict[str, str]] = list(tasks_api.get_tasks_for_section(
        section_gid=FOLLOW_UPS_UNDER_CONTRACT_SECTION,
        async_req=False,
        opts={})
    )

    under_contract_tasks: List[UnderContractTask] = \
        [UnderContractTask(address=raw_task['name'], gid=raw_task['gid']) for raw_task in raw_tasks]
    print(f'Found {len(under_contract_tasks)} under contract properties')

    today_str: str = get_today_str()

    # Filter only properties that we didn't analyze yet, i.e. the due date is not today (not set already)
    filtered_under_contract_tasks: List[UnderContractTask] = [
        under_contract_task for under_contract_task in under_contract_tasks
        if get_task_due_date(tasks_api, under_contract_task) != today_str
    ]
    print(f'Remain {len(filtered_under_contract_tasks)} under contract properties (not analyzed yet)')

    return filtered_under_contract_tasks
