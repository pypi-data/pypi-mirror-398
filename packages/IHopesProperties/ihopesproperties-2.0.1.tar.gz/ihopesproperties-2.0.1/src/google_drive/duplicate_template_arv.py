from typing import List

from googleapiclient.discovery import Resource

from google_drive.authenticator import get_google_services
from google_drive.comps_spread_sheet import CompsSpreadsheet
from google_drive.consts import ARV_TEMPLATE_FILE_ID, QUANTITY_OF_COMPS_TO_FILTER
from google_drive.spreadsheet_filler import write_comps_to_sheet, write_lead_property_info_to_sheet
from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty


def copy_google_sheet(service: Resource, source_file_id: str, new_file_name: str) -> CompsSpreadsheet:
    """
    Function to copy the file and rename it
    :param service:
    :param source_file_id:
    :param new_file_name:
    :return:
    """
    # Create a copy of the file
    copied_file = service.files().copy(
        fileId=source_file_id,
        body={'name': new_file_name}
    ).execute()

    print(f"File copied and renamed to: {copied_file['name']}")
    file_path: str = f'https://docs.google.com/spreadsheets/d/{copied_file["id"]}'
    return CompsSpreadsheet(
        file_id=copied_file['id'],
        file_path=file_path
    )


def save_as_template_arv(for_sale_property: ForSaleProperty, comps: List[SoldProperty], quantity_of_comps: int = QUANTITY_OF_COMPS_TO_FILTER) -> str:
    """
    Save the ARV template with the lead property and comps data.
    :param for_sale_property:
    :param comps:
    :param quantity_of_comps:
    :return:
    """
    drive_service: Resource = get_google_services().drive
    sheets_service: Resource = get_google_services().sheets

    # Copy the file and rename it
    comps_doc: CompsSpreadsheet = copy_google_sheet(
        service=drive_service,
        source_file_id=ARV_TEMPLATE_FILE_ID,
        new_file_name=for_sale_property.address.get_full_address()
    )

    # Write the lead property info to the sheet
    write_lead_property_info_to_sheet(
        service=sheets_service,
        sheet_id=comps_doc.file_id,
        for_sale_property=for_sale_property
    )

    updated_comps: List[SoldProperty] = comps[:quantity_of_comps]
    if quantity_of_comps < len(comps):
        print(f"Note: Only {quantity_of_comps} comps will be written to the sheet out of {len(comps)} available comps.")

    # Write comps to the sheet
    write_comps_to_sheet(
        service=sheets_service,
        sheet_id=comps_doc.file_id,
        comps=updated_comps
    )

    return comps_doc.file_path
