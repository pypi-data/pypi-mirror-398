from datetime import date
from typing import List, Dict

from asana import TasksApi

from flows.leads_cleaner_flow.leads_task import LeadsTask
from my_asana.authenticate import get_tasks_api
from my_asana.consts import LEADS_PROPERTIES_SECTION, PROPERTY_TASK_TEMPLATE_ID


def get_today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def get_task_due_date(tasks_api: TasksApi, leads_property: LeadsTask) -> str:
    return tasks_api.get_task(leads_property.gid, opts={})['due_on']


def get_leads_properties() -> List[LeadsTask]:
    tasks_api: TasksApi = get_tasks_api()
    raw_tasks: List[Dict[str, str]] = list(tasks_api.get_tasks_for_section(
        section_gid=LEADS_PROPERTIES_SECTION,
        async_req=False,
        opts={})
    )

    leads_tasks: List[LeadsTask] = \
        [LeadsTask(address=raw_task['name'], gid=raw_task['gid']) for raw_task in raw_tasks \
         if raw_task['gid'] != PROPERTY_TASK_TEMPLATE_ID]
    print(f'Found {len(leads_tasks)} leads properties')

    today_str: str = get_today_str()

    # Filter only properties that we didn't analyze yet, i.e. the due date is not today (not set already)
    filtered_leads_tasks: List[LeadsTask] = [
        leads_task for leads_task in leads_tasks
        if get_task_due_date(tasks_api, leads_task) != today_str
    ]
    print(f'Remain {len(filtered_leads_tasks)} leads properties (not analyzed yet)')

    return filtered_leads_tasks
