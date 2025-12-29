# Initialize the Apify client
from apify.skip_trace.owner_data import PropertyOwnerInfo, transform_skip_trace_results_to_property_owner_info
from apify.zillow_scrapers.common.client import MyApifyClient
from apify.zillow_scrapers.common.actor import Actor
from my_asana.comments_helper import add_comment_to_task, get_full_owner_details_message
from properties_defs.property_address import PropertyAddress


def skip_trace_property(property_address: PropertyAddress) -> PropertyOwnerInfo:
    apify_client: MyApifyClient = MyApifyClient(actor=Actor.SKIP_TRACE)

    # Prepare the Actor input
    run_input = {
        "max_results": 1,
        "street_citystatezip": [
            f"{property_address.address}; {property_address.city}, {property_address.state} {property_address.zip_code}"
        ],
    }

    items: list = apify_client.run_client(run_input=run_input)

    if len(items) > 1:
        raise ValueError(f"Expected only one item in the list, but got {len(items)} items.")

    owner_data: dict = items[0]
    owner_info: PropertyOwnerInfo = transform_skip_trace_results_to_property_owner_info(skip_trace_results=owner_data)

    return owner_info


if __name__ == "__main__":

    owner_info: PropertyOwnerInfo = (
        skip_trace_property(PropertyAddress.from_full_address("1310 Breining St, Pittsburgh, PA 15226"))
    )
    add_comment_to_task(
        task_id='1211795857061179',
        comment=get_full_owner_details_message(owner_info)
    )
