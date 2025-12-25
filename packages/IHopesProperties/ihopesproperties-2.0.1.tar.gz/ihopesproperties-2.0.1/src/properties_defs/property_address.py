from __future__ import annotations

from typing import Optional


class PropertyAddress:
    def __init__(self, address: str, city: str, state: str, zip_code: Optional[str] = None):
        self.address: str = address
        self.city: str = city
        self.state: str = state
        self.zip_code: str = zip_code

    def get_full_address(self) -> str:
        zip_code: str = self.zip_code if self.zip_code else ""
        return f"{self.address}, {self.city}, {self.state} {zip_code}"

    def get_address_without_zip_code(self) -> PropertyAddress:
        return PropertyAddress(self.address, self.city, self.state)

    @staticmethod
    def from_full_address(full_address: str):
        """
        Address can either be '439 William St, Mount, Oliver, PA 15210' or '439 William St, PA 15210'.
        :param full_address:
        :return:
        """
        address_parts = full_address.split(',')
        if len(address_parts) == 4:
            address = address_parts[0].strip()
            city = f'{address_parts[1].strip()}, {address_parts[2].strip()}'
            state_zip = address_parts[3].strip().split()
            state = state_zip[0]
            zip_code = state_zip[1]
        elif len(address_parts) == 3:
            address = address_parts[0].strip()
            city = address_parts[1].strip()
            state_zip = address_parts[2].strip().split()
            state = state_zip[0]
            zip_code = state_zip[1]
        else:
            raise ValueError(f"Invalid address format: {full_address}")
        return PropertyAddress(address, city, state, zip_code)
