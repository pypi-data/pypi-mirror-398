from enum import Enum

class ContingentStatus(Enum):
    UNDER_CONTRACT = "Under Contract"
    FOR_SALE = "For Sale"
    RECENTLY_SOLD = "Recently Sold"
    FOR_RENT = "For Rent"
    OFF_MARKET = "Off Market"