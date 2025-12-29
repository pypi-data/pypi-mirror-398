from __future__ import annotations
from typing import Optional

from googleapiclient.discovery import Resource

from google_drive.authenticator import get_google_services
from google_drive.consts import LEADS_ANALYSIS_FOLDER_ID


class CompsSpreadsheet:
    """
    Class representing a Google Spreadsheet for comps data.
    """
    def __init__(self, file_id: str, file_path: str):
        self.file_id = file_id
        self.file_path = file_path

    def __str__(self):
        return f"File ID: {self.file_id}, File path: {self.file_path}"

    @classmethod
    def from_property_address(cls, address: str) -> Optional[CompsSpreadsheet]:
        """
        Get a CompsSpreadsheet instance by property address.
        :param address: Full address of the property.
        :return: CompsSpreadsheet instance or None if not found.
        """
        drive_service: Resource = get_google_services().drive
        results = drive_service.files().list(
            q=f"'{LEADS_ANALYSIS_FOLDER_ID}' in parents and name = '{address}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false",
            spaces='drive',
            fields="nextPageToken, files(id, name)"
        ).execute()

        items = results.get('files', [])
        if not items:
            print(f"No files found for address: {address}")
            return None

        file_id = items[0]['id']
        file_path = f'https://docs.google.com/spreadsheets/d/{file_id}'

        return cls(file_id=file_id, file_path=file_path)