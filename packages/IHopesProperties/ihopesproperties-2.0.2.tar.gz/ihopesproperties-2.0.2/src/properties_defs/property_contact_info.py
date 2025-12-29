from __future__ import annotations

from typing import Optional


class ListingContactInfo:
    def __init__(self, name: Optional[str] = None, phone: Optional[str] = None,
                 email: Optional[str] = None, website: Optional[str] = None):
        self.name: str = name
        self.phone: str = phone
        self.email: Optional[str] = email
        self.website: Optional[str] = website
