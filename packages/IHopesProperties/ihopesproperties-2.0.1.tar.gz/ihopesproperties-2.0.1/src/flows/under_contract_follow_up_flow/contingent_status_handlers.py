from abc import ABC, abstractmethod
from typing import Type

from flows.common.contingent_status import ContingentStatus
from flows.under_contract_follow_up_flow.under_contract_task import UnderContractTask
from my_asana.comments_helper import get_up_for_sale_again_message, add_comment_to_task, \
    add_followers_to_task, get_property_sold_message, get_off_market_message, get_property_for_rent_message
from my_asana.consts import LEADS_PROPERTIES_SECTION, DECLINED_LEADS_SECTION, LISTING_EXPIRED_SECTION
from my_asana.users import randomly_select_user_id
from my_asana.utils import add_task_to_section, update_task



class AbstractContingentHandler(ABC):
    def __init__(self, under_contract_property: UnderContractTask):
        self.under_contract_property: UnderContractTask = under_contract_property

    @abstractmethod
    def handle(self):
        pass


class StillUnderContractHandler(AbstractContingentHandler):
    def __init__(self, under_contract_property: UnderContractTask):
        super().__init__(under_contract_property)

    def handle(self):
        print(f'Property is still under contract: {self.under_contract_property.address.get_full_address()}')


class RecentlySoldHandler(AbstractContingentHandler):
    def __init__(self, under_contract_property: UnderContractTask):
        super().__init__(under_contract_property)

    def handle(self):
        """
        Set the property as recently sold, including:
        1. Add a comment to the task (notify the property is sold)
        2. Mark the task as completed
        3. Add the task to the Declined section
        :param under_contract_property:
        :return:
        """
        print(f'Property is recently sold: {self.under_contract_property.address.get_full_address()}')

        # Add a comment
        add_comment_to_task(
            task_id=self.under_contract_property.gid,
            comment=get_property_sold_message()
        )

        # Mark the task as completed
        update_task(
            task_id=self.under_contract_property.gid,
            data={"completed": True}
        )

        # Add the task to the Declined section
        add_task_to_section(
            task_id=self.under_contract_property.gid,
            section_id=DECLINED_LEADS_SECTION,
        )


class ForSaleHandler(AbstractContingentHandler):
    def __init__(self, under_contract_property: UnderContractTask):
        super().__init__(under_contract_property)

    def handle(self):
        """
        Set the property as for sale again, including:
        1. Add followers (to make sure the tagging will directly notify them)
        2. Add a comment to the task (notify the property is up for sale again)
        3. Assign the task to a random user
        4. Add the task to the Leads section
        :param under_contract_property:
        :return:
            """
        print(f'Property is up for sale again: {self.under_contract_property.address.get_full_address()}')

        # Add followers
        add_followers_to_task(
            task_id=self.under_contract_property.gid
        )

        # Add a comment
        add_comment_to_task(
            task_id=self.under_contract_property.gid,
            comment=get_up_for_sale_again_message()
        )

        # Assign the task to a random user
        update_task(
            task_id=self.under_contract_property.gid,
            data={"assignee": randomly_select_user_id()}
        )

        # Add the task to the Leads section
        add_task_to_section(
            task_id=self.under_contract_property.gid,
            section_id=LEADS_PROPERTIES_SECTION,
            insert_at_the_top=True
        )

class ForRentHandler(AbstractContingentHandler):
    def __init__(self, under_contract_property: UnderContractTask):
        super().__init__(under_contract_property)

    def handle(self):
        """
        Set the property as for rent, including:
        1. Add a comment to the task (notify the property is for rent)
        2. Mark the task as completed
        3. Add the task to the Declined section
        :param under_contract_property:
        :return:
        """
        print(f'Property is for rent: {self.under_contract_property.address.get_full_address()}')

        # Add a comment
        add_comment_to_task(
            task_id=self.under_contract_property.gid,
            comment=get_property_for_rent_message()
        )

        # Mark the task as completed
        update_task(
            task_id=self.under_contract_property.gid,
            data={"completed": True}
        )

        # Add the task to the Declined section
        add_task_to_section(
            task_id=self.under_contract_property.gid,
            section_id=DECLINED_LEADS_SECTION,
        )

class OffMarketHandler(AbstractContingentHandler):
    def __init__(self, under_contract_property: UnderContractTask):
        super().__init__(under_contract_property)

    def handle(self):
        """
            Set the property as off market, including:
            1. Add a comment to the task
            2. Mark the task as completed
            3. Add the task to the Declined section
            :param under_contract_property:
            :return:
            """
        print(f'Property is off market: {self.under_contract_property.address.get_full_address()}')

        # Add a comment
        add_comment_to_task(
            task_id=self.under_contract_property.gid,
            comment=get_off_market_message()
        )

        # Add the task to the Listing Expired (Matt's Initiative) section
        add_task_to_section(
            task_id=self.under_contract_property.gid,
            section_id=LISTING_EXPIRED_SECTION,
        )

class ContingentStatusMapper:
    """
        Maps contingent statuses to their corresponding handler classes.
    """
    @staticmethod
    def get_handler(contingent_status: ContingentStatus) -> Type[AbstractContingentHandler]:
        handlers: dict[ContingentStatus, Type[AbstractContingentHandler]] = {
            ContingentStatus.UNDER_CONTRACT: StillUnderContractHandler,
            ContingentStatus.FOR_SALE: ForSaleHandler,
            ContingentStatus.RECENTLY_SOLD: RecentlySoldHandler,
            ContingentStatus.FOR_RENT: ForRentHandler,
            ContingentStatus.OFF_MARKET: OffMarketHandler
        }
        return handlers[contingent_status]