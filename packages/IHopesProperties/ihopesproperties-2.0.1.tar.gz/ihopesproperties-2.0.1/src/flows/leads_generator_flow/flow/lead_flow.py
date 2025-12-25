from typing import List, Tuple

from apify.zillow_scrapers.zillow_detail_scraper.on_the_fly_runner import generate_for_sale_property_from_address
from common.utils.logger import log
from comps_extractor.comps_generator import generate_comps
from flows.flows_meta import Flow
from my_asana.generate_tasks.tasks_generator import generate_new_property_task, GeneratedTask
from my_asana.utils import is_task_exists
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty


def address_based_lead_flow(address: str, flow: Flow) -> GeneratedTask:
    lead_property: ForSaleProperty = generate_for_sale_property_from_address(address=address)
    generated_task: GeneratedTask = lead_flow(
        lead_property=lead_property,
        flow=flow
    )
    return generated_task


def lead_flow(lead_property: ForSaleProperty, flow: Flow) -> GeneratedTask:
    address: str = lead_property.address.get_full_address()
    log(msg=f'Working on property: {address}')

    if is_task_exists(lead_property.address):
        log(msg=f"Task already exists for: {address}, stopping the process..")
        return GeneratedTask('','')

    #lead_property: ForSaleProperty = generate_for_sale_property_from_address(address=address)
    log(msg=f"Generated a new for sale property successfully: {lead_property}")

    comps: List[SoldProperty] = generate_comps(
        for_sale_property=lead_property,
        test_mode=False
    )
    log(f'Found total of {len(comps)} comps for {address}')

    if not comps:  # If no comps found, add to the no-comps list
        log(msg=f"No comps found for property: {address}.")

    generated_task: GeneratedTask = generate_new_property_task(
        for_sale_property=lead_property,
        comps=comps,
        flow=flow
    )
    log(msg=f'Generated Asana task for {address} with link: {generated_task.task_link}')

    return generated_task
