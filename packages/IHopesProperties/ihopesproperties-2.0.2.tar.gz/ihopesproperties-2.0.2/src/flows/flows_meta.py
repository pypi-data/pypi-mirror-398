from enum import Enum
from typing import List

from my_asana.consts import LISTING_EXPIRED_SECTION, LEADS_PROPERTIES_SECTION, PROPERTY_TASK_TEMPLATE_ID, \
    EXPIRED_PROPERTY_TASK_TEMPLATE_ID

class TaskPlaceHolder(Enum):
    ARV_DOC = "ARV Doc"
    PROPERTY_LINK = "Property Link"
    PROPERTY_MEDIA = "Property Media"
    EXPIRY_DATE = "Expiry Date"
    LAST_AP = "Last AP"
    SELLERS_NAME = "Seller's Name"
    SELLERS_CONTACT_INFO = "Seller's Contact Information"
    LISTING_AGENT_NAME = "Listing Agent Name"
    LISTING_AGENT_PHONE = "Listing Agent Phone"
    LISTING_AGENT_EMAIL = "Listing Agent Email"
    LISTING_OFFICE_NAME = "Listing Office Name"
    LISTING_OFFICE_PHONE = "Listing Office Phone"
    LISTING_OFFICE_EMAIL = "Listing Office Email"


class Flow(Enum):
    GENERATE_LEADS = (
        'Generate Leads Flow',
        LEADS_PROPERTIES_SECTION,
        PROPERTY_TASK_TEMPLATE_ID,
        [TaskPlaceHolder.ARV_DOC, TaskPlaceHolder.PROPERTY_LINK, TaskPlaceHolder.PROPERTY_MEDIA,
         TaskPlaceHolder.LISTING_AGENT_NAME, TaskPlaceHolder.LISTING_AGENT_PHONE, TaskPlaceHolder.LISTING_AGENT_EMAIL,
         TaskPlaceHolder.LISTING_OFFICE_NAME, TaskPlaceHolder.LISTING_OFFICE_PHONE, TaskPlaceHolder.LISTING_OFFICE_EMAIL]
    )
    LISTING_EXPIRED = (
        'Listing Expired Flow',
        LISTING_EXPIRED_SECTION,
        EXPIRED_PROPERTY_TASK_TEMPLATE_ID,
        [TaskPlaceHolder.ARV_DOC, TaskPlaceHolder.PROPERTY_LINK, TaskPlaceHolder.EXPIRY_DATE,
         TaskPlaceHolder.LAST_AP, TaskPlaceHolder.SELLERS_NAME, TaskPlaceHolder.SELLERS_CONTACT_INFO
         ]
    )

    def __init__(self, name: str, section_id: str, template_task_id: str,
                 template_task_place_holders: List[TaskPlaceHolder]):
        self.flow_name: str = name
        self.section_id: str = section_id
        self.template_task_id: str = template_task_id
        self.template_task_place_holders: List[TaskPlaceHolder] = template_task_place_holders
