import asana
from asana.rest import ApiException
from pprint import pprint

from my_asana.authenticate import get_api_client
from my_asana.consts import LEADS_PROJECT_ID

def get_sections_data():
    api_client = get_api_client()

    # create an instance of the API class
    sections_api_instance = asana.SectionsApi(api_client)

    opts = {
        'limit': 50, # int | Results per page. The number of objects to return per page. The value must be between 1 and 100.
        'opt_fields': "created_at,name,offset,path,project,project.name,projects,projects.name,uri", # list[str] | This endpoint returns a compact resource, which excludes some properties by default. To include those optional properties, set this query parameter to a comma-separated list of the properties you wish to include.
    }

    try:
        # Get sections in a project
        api_response = sections_api_instance.get_sections_for_project(LEADS_PROJECT_ID, opts)
        for data in api_response:
            pprint(data)
    except ApiException as e:
        print("Exception when calling SectionsApi->get_sections_for_project: %s\n" % e)


if __name__ == "__main__":
    get_sections_data()