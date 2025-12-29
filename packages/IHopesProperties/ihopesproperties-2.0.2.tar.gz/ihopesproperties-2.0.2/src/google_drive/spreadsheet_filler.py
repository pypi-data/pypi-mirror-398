from typing import List, Any, Tuple

from googleapiclient.discovery import Resource

from properties_defs.properties.for_sale_property import ForSaleProperty
from properties_defs.properties.sold_property import SoldProperty


def write_lead_property_info_to_sheet(service: Resource, sheet_id: str, for_sale_property: ForSaleProperty) -> None:
    """
    Writes the property information to the specified Google Sheet.
    :param service:
    :param sheet_id:
    :param for_sale_property:
    :return:
    """
    sheets = service.spreadsheets()

    # Fetch the sheet data to find where "Property Info" is located
    sheet_data = sheets.values().get(spreadsheetId=sheet_id, range='ARV & Comps').execute()
    values = sheet_data.get('values', [])

    # Prepare data for insertion
    property_data = [
        [
            for_sale_property.zillow_link,  # Property Link
            for_sale_property.address.get_full_address(),
            for_sale_property.listed_date,
            f"{for_sale_property.bedrooms}/{for_sale_property.bathrooms}",
            for_sale_property.sqft,
            for_sale_property.asking_price,
            "",  # Empty column currently (adjusted price in comps)
            "",  # Empty column currently (consider in comps)
            "",  # Condition (optional, if applicable)
            "",  # Special Features (optional, if applicable)
            for_sale_property.lot_sqft,
            for_sale_property.year_built
        ]
    ]

    # Write the property data to the sheet
    range_to_update = f'ARV & Comps!A2:L3'
    sheets.values().update(
        spreadsheetId=sheet_id,
        range=range_to_update,
        valueInputOption='RAW',
        body={'values': property_data}
    ).execute()


def write_comps_to_sheet(service: Resource, sheet_id: str, comps: List[SoldProperty]) -> int:
    """
    Writes and update the comps data to the specified Google Sheet.
    :param service: Google Sheets API resource.
    :param sheet_id: ID of the Google Sheet.
    :param comps: List of Property objects to write.
    :return: Number of new comps added to the sheet.
    """

    start_row: int = get_start_row_comps(service, sheet_id)
    end_row: int = get_end_row_comps(service, sheet_id, start_row)

    # Prepare data for insertion
    comps_data = [
        [
            comp.zillow_link,  # Property Link
            comp.address.get_full_address(),
            comp.sold_date,  # Listing Sold Date
            f"{comp.bedrooms}/{comp.bathrooms}",
            comp.sqft,  # House sqft
            comp.sold_price,  # Sold price
            comp.sold_price,  # Adjusted Price
            "",  # Condition (optional, if applicable)
            "",  # Special Features (optional, if applicable)
            comp.lot_sqft,  # Lot sqft
            comp.year_built,  # Year Built (optional, if applicable)
            comp.dist_from_lead,  # distance from lead property
        ]
        for comp in comps
    ]

    exclude_old_comps(service, sheet_id, start_row, end_row, comps_data)
    new_comps_number = update_new_comps(service, sheet_id, start_row, end_row, comps_data)

    return new_comps_number


def get_start_row_comps(service: Resource, sheet_id: str) -> int:
    """
    Returns the line number where the comps data starts in the Google Sheet.
    :param service: Google Sheets API resource.
    :param sheet_id: ID of the Google Sheet.
    :return: Line number for comps data.
    """
    sheets = service.spreadsheets()

    # Fetch the sheet data to find where "Comps" is located
    sheet_data = sheets.values().get(spreadsheetId=sheet_id, range='ARV & Comps').execute()
    values = sheet_data.get('values', [])

    # Locate the "Comps" row
    comps_row_index = next(
        (index for index, row in enumerate(values) if "Comps" in row), None
    )
    if comps_row_index is None:
        raise ValueError("Comps section not found in the template.")

    return comps_row_index + 3  # Three rows below "Comps" for headers and since it's 0-based index


def get_end_row_comps(service: Resource, sheet_id: str, start_row: int, max_rows_to_check: int = 100) -> int:
    """
    Returns the last row number for comps data in the Google Sheet.
    :param service: Google Sheets API resource.
    :param sheet_id: ID of the Google Sheet.
    :param start_row: Starting row number for comps data.
    :param max_rows_to_check: Maximum number of rows to check for comps data.
    :return: Last row number for comps data.
    """
    sheets = service.spreadsheets()

    range_to_check = f'ARV & Comps!A{start_row}:K{start_row + max_rows_to_check - 1}'
    sheet_rows = sheets.values().get(
        spreadsheetId=sheet_id,
        range=range_to_check
    ).execute().get('values', [])

    # Find the end row where the first cell is empty
    i = 0
    for i, row in enumerate(sheet_rows):
        if not row or not row[0].strip():
            break
    end_row = start_row + i -1 # The end row is the last filled row, so we subtract 1

    return end_row


def exclude_old_comps(service: Resource, sheet_id: str, start_row: int, end_row: int, comps_data: List[List[Any]]):
    """
    Excludes old comps from the Google Sheet by marking them as unconsidered.
    :param service: Google Sheets API resource.
    :param sheet_id: ID of the Google Sheet.
    :param start_row: Starting row number for comps data.
    :param end_row: Ending row number for comps data.
    :param comps_data: List of comps data to compare against.
    :return:
    """
    sheets = service.spreadsheets()

    sheet_data = f'ARV & Comps!A{start_row}:K{end_row}'
    sheet_rows = sheets.values().get(
        spreadsheetId=sheet_id,
        range=sheet_data
    ).execute().get('values', [])

    # Extract all zillow_link values from comps_data
    zillow_links: List[str] = [row[0] for row in comps_data]

    # Collect row numbers to update
    rows_to_update = []
    for i, sheet_row in enumerate(sheet_rows):
        current_row = start_row + i
        if current_row > end_row:
            break
        first_cell = sheet_row[0] if sheet_row else ""
        if first_cell not in zillow_links:
            rows_to_update.append(current_row)

    row_index_letter_tup: Tuple[int, str] = find_comps_column_by_header_name(
        service=service,
        sheet_id=sheet_id,
        header_name="Consider?"
    )
    requests = [
        {
            "range": f"ARV & Comps!{row_index_letter_tup[1]}{row}",
            "values": [[False]]
        }
        for row in rows_to_update
    ]

    # Execute the batch update
    if requests:
        sheets.values().batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "valueInputOption": "RAW",
                "data": requests
            }
        ).execute()
        print(f"Unconsidered comps updated in rows: {rows_to_update}")


def update_new_comps(service: Resource, sheet_id: str, start_row: int, end_row: int, comps_data: List[List[Any]]) -> int:
    """
    Updates the new comps data in the specified Google Sheet.
    :param service: Google Sheets API resource.
    :param sheet_id: ID of the Google Sheet.
    :param start_row: Starting row number for existing comps data.
    :param end_row: Ending row number for existing comps data.
    :param comps_data: List of Property objects to update.
    :return: Number of new comps added to the sheet.
    """
    sheets = service.spreadsheets()
    sheet_data = f'ARV & Comps!A{start_row}:K{end_row}'
    sheet_rows = sheets.values().get(
        spreadsheetId=sheet_id,
        range=sheet_data
    ).execute().get('values', [])

    # Extract existing zillow_link values
    existing_zillow_links: List[str] = [row[0] for row in sheet_rows if row]
    # Extract all zillow_link values from comps_data
    zillow_links: List[str] = [row[0] for row in comps_data]

    # Find new comps that are not already in the sheet
    new_comps_data: List[List[Any]] = \
        [comp for comp, link in zip(comps_data, zillow_links) if link not in existing_zillow_links]

    # There is no option to skip the Consider column without overriding it,
    # and hence - we need to split the writing into 2 parts.

    # Find Consider column
    row_index_letter_tup: Tuple[int, str] = find_comps_column_by_header_name(
        service=service,
        sheet_id=sheet_id,
        header_name="Consider?"
    )

    # Split data into left and right parts (skipping the Consider? column itself)
    left_data = [row[:row_index_letter_tup[0]] for row in new_comps_data]
    right_data = [row[row_index_letter_tup[0]:] for row in new_comps_data]

    # If there are existing rows, we need to append new data
    if start_row != end_row:
        end_row += 1

    new_comps_end_row: int = end_row + len(new_comps_data) - 1

    # Left range: A → column before Consider?
    start_col: str = 'A'
    end_col: str = chr(ord(row_index_letter_tup[1]) - 1)  # Until, exclusive
    left_range = f'ARV & Comps!{start_col}{end_row}:{end_col}{new_comps_end_row}'

    # Right range: column after Consider? → last col
    start_col: str = chr(ord(row_index_letter_tup[1]) + 1)  # After, exclusive
    end_col: str = 'M'
    right_range = f'ARV & Comps!{start_col}{end_row}:{end_col}{new_comps_end_row}'

    # Write the comps data to the sheet
    sheets.values().batchUpdate(
        spreadsheetId=sheet_id,
        body={
            "valueInputOption": "RAW",
            "data": [
                {"range": left_range, "values": left_data},
                {"range": right_range, "values": right_data},
            ]
        }
    ).execute()
    # range_to_update = f'ARV & Comps!A{end_row}:L{end_row + len(new_comps_data) - 1}'
    # sheets.values().update(
    #     spreadsheetId=sheet_id,
    #     range=range_to_update,
    #     valueInputOption='RAW',
    #     body={'values': new_comps_data}
    # ).execute()

    print(f"{len(new_comps_data)} new comps added to the sheet")
    return len(new_comps_data)

def find_comps_column_by_header_name(service: Resource, sheet_id: str, header_name: str) -> tuple[int, str]:
    """
    Finds the column letter index of a given header name in the 'ARV & Comps' sheet.
    :param service: Google Sheets API resource.
    :param sheet_id: ID of the Google Sheet.
    :param header_name: Name of the header to find.
    :return: Column index letter (e.g., 'A', 'B', etc.) or an empty string if not found.
    """
    sheets = service.spreadsheets()
    header_row_number = get_start_row_comps(service, sheet_id) - 1  # Assuming headers are in the row before the comps start
    range_to_check = f'ARV & Comps!A{header_row_number}:ZZ{header_row_number}'
    sheet_data = sheets.values().get(
        spreadsheetId=sheet_id,
        range=range_to_check
    ).execute().get('values', [])
    if not sheet_data:
        return -1, ""
    headers = sheet_data[0]
    for index, header in enumerate(headers):
        if header == header_name:
            return index, index_to_column_letter(index)
    return -1, ""  # Return empty string if header not found

def index_to_column_letter(index: int) -> str:
    """
    Converts a zero-based column index to a column letter (e.g., 0 -> 'A', 25 -> 'Z', 26 -> 'AA').
    :param index: Zero-based column index.
    :return: Column letter.
    """
    column_letter = ""
    while index >= 0:
        column_letter = chr(index % 26 + 65) + column_letter
        index = index // 26 - 1
    return column_letter