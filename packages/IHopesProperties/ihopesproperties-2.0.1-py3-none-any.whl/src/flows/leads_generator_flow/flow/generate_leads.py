from typing import List

from tqdm import tqdm

from common.utils.logger import log
from flows.common.leads_filters.filters import apply_filters, leads_filters
from flows.flows_meta import Flow
from flows.leads_generator_flow.flow.lead_flow import lead_flow
from flows.leads_generator_flow.flow.lead_source import LeadQuerySource, LeadsQuerySourcesHolder
from flows.leads_generator_flow.rentcast.fetch_for_sale_properties import fetch_active_for_sale_properties
from my_asana.generate_tasks.tasks_generator import GeneratedTask
from properties_defs.properties.for_sale_property import ForSaleProperty


def run_generate_leads_flow():
    print('Main flow - START!')
    for lead_source in LeadsQuerySourcesHolder().leads_sources:
        generate_single_source_leads(lead_source=lead_source)


def generate_single_source_leads(lead_source: LeadQuerySource) -> None:
    """
    Generate leads for a single source
    :param lead_source:
    :return:
    """
    log(msg=f'Fetching active for sale properties for {lead_source.to_string()}')
    filtered_for_sale_properties: List[ForSaleProperty] = get_active_for_sale_properties(lead_source)

    # Iterate over the properties and generate tasks
    for for_sale_property in tqdm(filtered_for_sale_properties, desc="Processing"):
        try:
            generated_tasl: GeneratedTask = lead_flow(
                lead_property=for_sale_property,
                flow=Flow.GENERATE_LEADS
            )
            if generated_tasl.task_link:
                log(msg=f'Property link: {generated_tasl.task_link}')
            else:
                log(msg=f'No task generated for {for_sale_property.address.get_full_address()}')
        except Exception as e:
            log(msg=f'Failed to process property: {for_sale_property.address.get_full_address()} [error={e}]')


def get_active_for_sale_properties(lead_source: LeadQuerySource) -> List[ForSaleProperty]:
    """
    Get active for sale properties for a given lead source, filtered by our system filters.
    :param lead_source:
    :return:
    """
    curr_lead_source_properties: List[ForSaleProperty] = fetch_active_for_sale_properties(
        lead_source=lead_source
    )
    log(msg=f'Fetched {len(curr_lead_source_properties)} active for sale properties for {lead_source.to_string()}')

    filtered_for_sale_properties: List[ForSaleProperty] = apply_filters(
        for_sale_properties=curr_lead_source_properties,
        filters=leads_filters
    )

    return filtered_for_sale_properties


if __name__ == '__main__':
    run_generate_leads_flow()
