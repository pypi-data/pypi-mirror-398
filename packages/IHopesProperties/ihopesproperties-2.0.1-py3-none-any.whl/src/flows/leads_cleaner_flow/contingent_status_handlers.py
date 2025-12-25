from abc import ABC, abstractmethod
from typing import Type

from flows.common.contingent_status import ContingentStatus
from flows.leads_cleaner_flow.leads_task import LeadsTask
from my_asana.comments_helper import add_comment_to_task, get_property_for_rent_message, get_off_market_message
from my_asana.consts import FOLLOW_UPS_UNDER_CONTRACT_SECTION, DECLINED_LEADS_SECTION, LISTING_EXPIRED_SECTION
from my_asana.users import randomly_select_user_id
from my_asana.utils import update_task, add_task_to_section


class AbstractContingentHandler(ABC):
    def __init__(self, leads_property: LeadsTask):
        self.leads_property: LeadsTask = leads_property

    def handle(self):
        from datetime import date

        # Update the due date to today
        today: str = date.today().strftime("%Y-%m-%d")
        update_task(
            task_id=self.leads_property.gid,
            data={"due_on": today}
        )

        self._handle()

    @abstractmethod
    def _handle(self):
        pass

class StillForSaleHandler(AbstractContingentHandler):
    def __init__(self, leads_property: LeadsTask):
        super().__init__(leads_property)

    def _handle(self):
        print(f'Property is still for sale: {self.leads_property.address.get_full_address()}')


class RecentlyUnderContractHandler(AbstractContingentHandler):
    def __init__(self, leads_property: LeadsTask):
        super().__init__(leads_property)

    def _handle(self):
        """
            Set the property as under contract, including:
            1. Assign the task to a random user
            2. Move the task to the Follow Ups (Under Contract) section
            3. Update the due date to today
        """
        print(f'Property has recently gone under contract: {self.leads_property.address.get_full_address()}')

        # Assign the task to a random user
        update_task(
            task_id=self.leads_property.gid,
            data={"assignee": randomly_select_user_id()}
        )

        # Move the task to the Follow Ups (Under Contract) section
        add_task_to_section(
            task_id=self.leads_property.gid,
            section_id=FOLLOW_UPS_UNDER_CONTRACT_SECTION,
        )


class RecentlySoldHandler(AbstractContingentHandler):
    def __init__(self, leads_property: LeadsTask):
        super().__init__(leads_property)

    def _handle(self):
        """
            Set the property as sold, including:
            1. Move the task to the Declined section
            2. Mark the task as completed
        """
        print(f'Property has recently been sold: {self.leads_property.address.get_full_address()}')

        # Mark the task as completed
        update_task(
            task_id=self.leads_property.gid,
            data={"completed": True}
        )

        # Move the task to the Declined section
        add_task_to_section(
            task_id=self.leads_property.gid,
            section_id=DECLINED_LEADS_SECTION,
        )

class RecentlyForRentHandler(AbstractContingentHandler, ABC):
    def __init__(self,  leads_property: LeadsTask):
        super().__init__(leads_property)

    def _handle(self):
        """
        Set the property as for rent, including:
        1. Add a comment to the task
        2. Mark the task as completed
        3. Add the task to the Declined section
        """
        print(f'Property is for rent: {self.leads_property.address.get_full_address()}')

        # Add a comment
        add_comment_to_task(
            task_id=self.leads_property.gid,
            comment=get_property_for_rent_message()
        )

        # Mark the task as completed
        update_task(
            task_id=self.leads_property.gid,
            data={"completed": True}
        )

        # Add the task to the Declined section
        add_task_to_section(
            task_id=self.leads_property.gid,
            section_id=DECLINED_LEADS_SECTION,
        )


class RecentlyOffMarketHandler(AbstractContingentHandler):
    def __init__(self, leads_property: LeadsTask):
        super().__init__(leads_property)

    def _handle(self):
        print(f'Property has recently been off market: {self.leads_property.address.get_full_address()}')

        # Add a comment
        add_comment_to_task(
            task_id=self.leads_property.gid,
            comment=get_off_market_message()
        )

        # Move the task to the Listing Expired (Matt's Initiative) section
        add_task_to_section(
            task_id=self.leads_property.gid,
            section_id=LISTING_EXPIRED_SECTION,
        )


class ContingentStatusMapper:
    """
        Maps contingent statuses to their corresponding handler classes.
    """
    @staticmethod
    def get_handler(contingent_status: ContingentStatus) -> Type[AbstractContingentHandler]:
        handlers: dict[ContingentStatus, Type[AbstractContingentHandler]] = {
            ContingentStatus.FOR_SALE: StillForSaleHandler,
            ContingentStatus.UNDER_CONTRACT: RecentlyUnderContractHandler,
            ContingentStatus.RECENTLY_SOLD: RecentlySoldHandler,
            ContingentStatus.FOR_RENT: RecentlyForRentHandler,
            ContingentStatus.OFF_MARKET: RecentlyOffMarketHandler
        }
        return handlers[contingent_status]