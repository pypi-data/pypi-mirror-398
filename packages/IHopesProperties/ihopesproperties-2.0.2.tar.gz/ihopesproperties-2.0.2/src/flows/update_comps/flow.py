from typing import List

from googleapiclient.discovery import Resource

from apify.zillow_scrapers.zillow_detail_scraper.on_the_fly_runner import generate_for_sale_property_from_address
from comps_extractor.comps_generator import generate_comps
from google_drive.authenticator import get_google_services
from google_drive.comps_spread_sheet import CompsSpreadsheet
from google_drive.spreadsheet_filler import write_comps_to_sheet
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty


def address_based_comps_update_flow(address: str) -> int:
    """
    Function to update comps for an existing lead by a given address.
    :param address: Address of the property.
    :return: Number of new comps added to the sheet.
    """
    sheets_service: Resource = get_google_services().sheets

    property_google_sheet: CompsSpreadsheet = CompsSpreadsheet.from_property_address(
        address=address
    )

    if not property_google_sheet:
        raise ValueError(f"No Google Sheet found for address: {address}")

    lead_property: ForSaleProperty = generate_for_sale_property_from_address(address=address)

    comps: List[SoldProperty] = generate_comps(
        for_sale_property=lead_property,
        test_mode=False
    )

    print(property_google_sheet)

    return write_comps_to_sheet(service=sheets_service,
                         sheet_id=property_google_sheet.file_id,
                         comps=comps)
