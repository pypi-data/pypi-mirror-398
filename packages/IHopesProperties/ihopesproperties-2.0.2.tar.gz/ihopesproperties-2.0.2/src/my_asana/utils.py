from functools import lru_cache
from typing import List, Dict

from common.addresses_utils.address_maniplator import get_all_possible_addresses
from my_asana.authenticate import get_tasks_api
from my_asana.consts import LEADS_PROJECT_ID, PROPERTY_TASK_TEMPLATE_ID
from properties_defs.property_address import PropertyAddress


@lru_cache(maxsize=1)
def get_asana_tasks(project_id: str) -> List[Dict[str, str]]:
    print(f"Fetching tasks from Asana API for project {project_id}...")
    tasks_api = get_tasks_api()
    tasks = tasks_api.get_tasks_for_project(project_id, opts={})
    return list(tasks)


def is_task_exists(property_address: PropertyAddress, soft_verification: bool = False) -> bool:
    tasks = get_asana_tasks(LEADS_PROJECT_ID)

    possible_addresses: List[str] = \
        [address.get_full_address() for address in get_all_possible_addresses(address=property_address)]

    for task in tasks:
        for address in possible_addresses:
            if soft_verification:
                if address in task['name']:
                    print(f"Task already exists for: {address}")
                    return True
            else:
                if task['name'] == address :
                    print(f"Task already exists for: {property_address}")
                    return True

    return False


def add_task_to_section(task_id: str, section_id: str, project_id: str = LEADS_PROJECT_ID,
                        insert_at_the_top: bool = False):
    """
    Add a task to a specific section in a project
    :param task_id: task ID to add
    :param section_id: section ID to add the task to
    :param project_id: project ID to add the task to
    :param insert_at_the_top: boolean to insert the task at the top of the section
    :return:
    """
    if project_id != LEADS_PROJECT_ID and insert_at_the_top:
        raise RuntimeError("insert_at_the_top can only be used with the LEADS_PROJECT_ID project."
                           " When using a different project, you should set insert_at_the_top to False.")

    tasks_api = get_tasks_api()

    data = {
        "data": {
            "project": project_id,
        }
    }
    if insert_at_the_top:
        data['data']['insert_after'] = PROPERTY_TASK_TEMPLATE_ID
    else:
        data['data']['section'] = section_id

    # Add the task to the project and section using the 'add_project_for_task' method
    tasks_api.add_project_for_task(task_gid=task_id, body=data)
    print(f'Added task {task_id} to section {section_id}')


def update_task(task_id: str, data: dict):
    """
    Update a task using the Asana API
    :param task_id: task ID to update
    :param data: data to update the task with
    :return:
    """
    tasks_api = get_tasks_api()
    tasks_api.update_task(
        task_gid=task_id,
        body={"data": data},
        opts={}
    )
    _costume_update_task_output(task_id, data)

def _costume_update_task_output(task_id: str, data: dict):
    """
    Custom output for the update_task function
    :param task_id: task ID to update
    :param data: data to update the task with
    :return:
    """
    str_output: str = f'Updated task {task_id}'

    if 'assignee' in data:
        str_output += f' with assignee {data["assignee"]}'
    if 'due_on' in data:
        str_output += f' with due date {data["due_on"]}'
    if 'completed' in data:
        str_output += f' as completed'

    print(str_output)