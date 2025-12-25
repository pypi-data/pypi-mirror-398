from typing import Optional, List
import streamlit as st
import pandas as pd
from tqdm import tqdm

from apify.skip_trace.owner_data import PropertyOwnerInfo
from apify.skip_trace.skip_trace_actor import skip_trace_property
from apify.zillow_scrapers.zillow_detail_scraper.on_the_fly_runner import generate_for_sale_property_from_address
from flows.common.contingent_status import ContingentStatus
from flows.common.leads_filters.abstract_filter import LeadsFilter
from flows.common.leads_filters.bedrooms_filter import BEDROOMS_FILTER
from flows.common.leads_filters.filters import apply_filters
from flows.common.leads_filters.desired_neighborhoods_filter import DESIRED_NEIGHBORHOODS_FILTER
from flows.common.leads_filters.property_sqft_filter import SQFT_FILTER
from flows.flows_meta import Flow
from flows.leads_generator_flow.flow.lead_flow import lead_flow
from common.geo_utils.zip_code_finder import find_zip_code
from my_asana.comments_helper import add_comment_to_task, get_full_owner_details_message
from my_asana.consts import LEADS_PROJECT_ID
from my_asana.generate_tasks.tasks_generator import GeneratedTask
from my_asana.utils import is_task_exists, get_asana_tasks
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.property_address import PropertyAddress

listing_expired_filters: List[LeadsFilter] = [
    DESIRED_NEIGHBORHOODS_FILTER, # Has to be the first filter
    #ASKING_PRICE_FILTER,
    BEDROOMS_FILTER,
    SQFT_FILTER
]

def is_within_last_given_weeks(last_event_date: str, weeks: int) -> bool:
    from datetime import datetime, timedelta

    date_obj = datetime.strptime(last_event_date, "%Y-%m-%d").date()

    two_weeks_ago = datetime.today().date() - timedelta(weeks=weeks)

    if two_weeks_ago <= date_obj <= datetime.today().date():
        print(f"Date is within the last {weeks} weeks.")
        return True
    else:
        print(f"Date is not within the last {weeks} weeks - {last_event_date}")
        return False


def run_listing_expired_flow(expired_listings_df: pd.DataFrame, stop_on_the_first_already_existing_property: bool,
                             expired_weeks_back: int = 4):
    # Counters for data analysis
    total_properties: int = len(expired_listings_df)
    outside_neighborhoods_filtered: List[str] = []
    non_off_market_status_filtered: int = 0
    inside_pittsburgh_filtered: int = 0
    not_in_last_weeks_filtered: int = 0
    can_not_find_zip_code: int = 0
    succeeded: int = 0

    status = st.empty()
    progress_bar = st.progress(0.0)

    status.write(f"Starting listing expired flow for a total of {len(expired_listings_df)} properties")
    for index, row in tqdm(expired_listings_df.iterrows()):
        print(f'Property {index+1}/{total_properties}')
        status.text(f"Processing property {index + 1}/{len(expired_listings_df)}...")
        progress_bar.progress((index + 1)/len(expired_listings_df))

        property_address: PropertyAddress = PropertyAddress(
            address=row['Address'],
            city=row['City'],
            state='PA',
            #No zip_code available when exporting as csv from OneHome
        )
        print(f'Working on {property_address.get_full_address()}....')

        ######### Filter 1 #########
        # We are getting a lot of properties in out-of-pittsburgh neighborhoods, filtering it quickly here to save
        # running time and costs. Using here valid_outside_city and not is_in_desired_neighborhood
        # as we don't have zip code yet and hence cannot check inner city zip codes.
        if not DESIRED_NEIGHBORHOODS_FILTER.valid_outside_city(property_address):
            print(f'Property {property_address.get_full_address()} not in a desired outside city neighborhood,'
                  f' skipping..')
            outside_neighborhoods_filtered.append(property_address.city)
            continue

        # Check if we already have a task for this property. Continue to next property or exit entirely
        # based on @stop_on_the_first_already_existing_property
        if is_task_exists(property_address=property_address, soft_verification=True):
            if stop_on_the_first_already_existing_property:
                break
            else:
                continue

        # Fetch zip code based on get location (lat/long) and Cencus DB
        zip_code: Optional[str] = find_zip_code(property_address)
        if not zip_code:
            print(f'Can not find zip code, skipping {property_address.get_full_address()}...')
            can_not_find_zip_code += 1
            continue
        property_address.zip_code = zip_code

        ######### Filter 2 #########
        # Validating the address again after retrieval of the zip code,
        # this time with the broader is_in_desired_neighborhood method
        if not DESIRED_NEIGHBORHOODS_FILTER.is_in_desired_neighborhood(property_address):
            # Should not happen basically as OneHome is not using Pittsburgh as a city name but rather the actual
            # neighborhoods (and for outside city we already filetered in the beginning)
            print(f'######### Filtered property based on ZIP code ########')
            print(f'Property {property_address.get_full_address()} not in a desired neighborhood, skipping..')
            inside_pittsburgh_filtered +=1
            continue

        # Scrape zillow and generate for sale property only after address validations
        lead_property: Optional[ForSaleProperty] = generate_for_sale_property_from_address(
            address=property_address.get_full_address()
        )
        if not lead_property:
            print(f'Skipping on {property_address.get_full_address()} - could not generate for sale property')
            continue
        # Taking last listing price from OneHome data
        lead_property.last_listing_price = row['Price']

        ######### Filter 3 #########
        # Filtering out properties that are under contract/for sale again
        property_status: ContingentStatus = lead_property.get_contingency_status()
        if property_status is not ContingentStatus.OFF_MARKET:
            print(f'For property {property_address.get_full_address()}, '
                  f'got status {property_status.value}, hence skipping...')
            non_off_market_status_filtered += 1
            continue

        ######### Filter 4 #########
        # We are getting some real old ones for some reason, discover via price_history the last event_date
        if not is_within_last_given_weeks(lead_property.last_event_date, weeks=expired_weeks_back):
            not_in_last_weeks_filtered += 1
            continue

        ######### Filter 5 #########
        filtered_properties: List[ForSaleProperty] = apply_filters(
            for_sale_properties=[lead_property],
            filters=listing_expired_filters
        )
        if not filtered_properties:
            continue

        # Fetch owner info
        owner_info: PropertyOwnerInfo = skip_trace_property(property_address=lead_property.address)
        lead_property.owner_info = owner_info

        generated_task: GeneratedTask = lead_flow(
            lead_property=lead_property,
            flow=Flow.LISTING_EXPIRED
        )

        add_comment_to_task(
            task_id=generated_task.task_id,
            comment=get_full_owner_details_message(owner_info)
        )

        succeeded += 1
        print(f'For property {property_address.get_full_address()} generated task - {generated_task.task_link}')

    print(f'Out of total of {total_properties} properties - '
          f'\n{len(outside_neighborhoods_filtered)} properties filtered as outside Pittsburgh'
          f'\n{inside_pittsburgh_filtered} properties filtered as inside Pittsburgh'
          f'\n{non_off_market_status_filtered} properties filtered as non-off market (for sale/sold)'
          f'\n{not_in_last_weeks_filtered} properties filtered as their last status update '
          f'is not in the last {expired_weeks_back} weeks '
          f'\n{can_not_find_zip_code} properties filtered as could not infer their zip code'
          f'\n##### {succeeded} properties succeeded and task generated in Asana ######')

    print(f'Filtered neighborhoods...')
    print(",".join(list(set(outside_neighborhoods_filtered))))

    status.write(f"Finished listing expired flow ✅")


def update_agent_info(lead_property: ForSaleProperty, row):
    """
    We sometime get different name/phone number between zillow and MLS data (from Matt).
    Currently - listing both of them in the task description.
    """
    # Update agent name
    if lead_property.listing_agent.name:
        if lead_property.listing_agent.name != row['Contact']:
            lead_property.listing_agent.name += f'/from MLS - {row["Contact"]}'
    else:
        lead_property.listing_agent.name = f'{row["Contact"]}'
    # Update agent phone number
    if lead_property.listing_agent.phone:
        if lead_property.listing_agent.phone != row['Contact Phone']:
            lead_property.listing_agent.name += f'/from MLS - {row["Contact Phone"]}'
    else:
        lead_property.listing_agent.name = f'{row["Contact Phone"]}'


if __name__ == "__main__":
    expired_listings_csv: str = '/Users/oriperi/Documents/Ori/25To40/Repo/src/flows/listing_expired_flow/Expired_Listings_11_4_25.csv'
    df: pd.DataFrame = pd.read_csv(expired_listings_csv)
    #df = df.loc[df["Address"] == "411 Horning Road"].head(1)
    run_listing_expired_flow(expired_listings_df=df, stop_on_the_first_already_existing_property=False)
