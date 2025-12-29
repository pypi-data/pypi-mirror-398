from dataclasses import dataclass
from typing import List, Tuple

from asana.rest import ApiException

from apify.skip_trace.owner_data import PhoneNumber
from flows.flows_meta import Flow, TaskPlaceHolder
from google_drive.duplicate_template_arv import save_as_template_arv
from my_asana.authenticate import get_tasks_api
from my_asana.consts import LEADS_PROJECT_ID
from my_asana.utils import add_task_to_section
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty
from zillow.property_getter import construct_zillow_basic_property_url

@dataclass
class GeneratedTask:
    task_id: str
    task_link: str



def generate_new_property_task(for_sale_property: ForSaleProperty, comps: List[SoldProperty], flow: Flow) \
        -> GeneratedTask:
    # Create API instance
    property_address: str = for_sale_property.address.get_full_address()

    try:
        # Get the source task
        tasks_api = get_tasks_api()
        template_task = tasks_api.get_task(flow.template_task_id, opts=[])
        template_description = template_task['notes']

        for place_holder in flow.template_task_place_holders:
            if place_holder.value in template_description:
                print(f"Found placeholder: {place_holder.value}")
                if place_holder is TaskPlaceHolder.ARV_DOC:
                    updated_description: str = save_as_template_arv(for_sale_property, comps)
                elif place_holder is TaskPlaceHolder.PROPERTY_LINK:
                    updated_description: str = construct_zillow_basic_property_url(property_address)
                elif place_holder is TaskPlaceHolder.PROPERTY_MEDIA:
                    updated_description: str = ""
                elif place_holder is TaskPlaceHolder.EXPIRY_DATE:
                    updated_description: str = for_sale_property.last_event_date
                elif place_holder is TaskPlaceHolder.LAST_AP:
                    updated_description: str = for_sale_property.last_listing_price
                elif place_holder is TaskPlaceHolder.SELLERS_NAME:
                    updated_description: str = \
                        f'{for_sale_property.owner_info.first_name} {for_sale_property.owner_info.last_name}'
                elif place_holder is TaskPlaceHolder.SELLERS_CONTACT_INFO:
                    numbers: List[PhoneNumber] = for_sale_property.owner_info.phone_numbers
                    updated_description: str = numbers[0].number if numbers else ""
                elif place_holder is TaskPlaceHolder.LISTING_AGENT_NAME:
                    updated_description: str = for_sale_property.listing_agent.name
                elif place_holder is TaskPlaceHolder.LISTING_AGENT_PHONE:
                    updated_description: str = for_sale_property.listing_agent.phone
                elif place_holder is TaskPlaceHolder.LISTING_AGENT_EMAIL:
                    updated_description: str = for_sale_property.listing_agent.email
                elif place_holder is TaskPlaceHolder.LISTING_OFFICE_NAME:
                    updated_description: str = for_sale_property.listing_office.name
                elif place_holder is TaskPlaceHolder.LISTING_OFFICE_PHONE:
                    updated_description: str = for_sale_property.listing_office.phone
                elif place_holder is TaskPlaceHolder.LISTING_OFFICE_EMAIL:
                    updated_description: str = for_sale_property.listing_office.email
                else:
                    raise ValueError(f"Unknown placeholder: {place_holder.value}")

                template_description = template_description.replace(
                    f'{place_holder.value}:',
                    f"{place_holder.value}: {updated_description}"
                )
            else:
                print(f"Placeholder not found: {place_holder.value}. Having an issue here.")

        # Create a new task
        new_task_body = {
            "data": {
                "name": property_address,
                "notes": template_description,
                "projects": LEADS_PROJECT_ID,  # Copy the same project association
            }
        }

        new_task = tasks_api.create_task(new_task_body, opts=[])
        add_task_to_section(task_id=new_task["gid"], section_id=flow.section_id)
        print("New task created successfully!")
        print("New Task ID:", new_task['gid'])

        task_link: str = f"https://app.asana.com/0/{LEADS_PROJECT_ID}/{new_task['gid']}/f"
        print(f'Task link for {property_address}: {task_link}')

        return GeneratedTask(task_id=new_task['gid'], task_link=task_link)

    except ApiException as e:
        print("Error occurred:", e)
