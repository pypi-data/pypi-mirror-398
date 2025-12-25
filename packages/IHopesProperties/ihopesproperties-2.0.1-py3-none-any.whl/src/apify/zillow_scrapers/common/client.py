from typing import Optional

from apify_client import ApifyClient

from apify.zillow_scrapers.common.config import APIFY_API_TOKEN
from apify.zillow_scrapers.common.actor import Actor


def get_apify_client() -> ApifyClient:
    client = ApifyClient(APIFY_API_TOKEN)
    return client



class MyApifyClient:

    def __init__(self, actor: Actor):
        self.client = ApifyClient(APIFY_API_TOKEN)
        self.actor: Actor = actor

    def run_client(self, run_input: dict, test_dataset_id: Optional[str] = None) -> Optional[list]:
        """
        Run one of the Apify actors to scrape zillow data.
        :param test_dataset_id: If running in test mode, use this dataset ID.
        :param run_input:
        :return:
        """
        if test_dataset_id:
            dataset_id: str = test_dataset_id
        else:
            run = self.client.actor(self.actor.value).call(run_input=run_input)
            dataset_id: str = run["defaultDatasetId"]

            if 'scraped 0 items' in run.get('statusMessage',""):
                print("No data found in the search results.")
                return None

        print("Check your data here: https://console.apify.com/storage/datasets/" + dataset_id)

        items: list = self.client.dataset(dataset_id).list_items().items
        if not items:
            print("No items found in the dataset.")
            return None

        return items
