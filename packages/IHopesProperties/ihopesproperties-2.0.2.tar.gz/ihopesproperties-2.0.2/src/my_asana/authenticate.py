import asana
from asana import TasksApi, ApiClient, StoriesApi

from my_asana.consts import PERSONAL_ACCESS_TOKEN


def get_tasks_api() -> TasksApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    tasks_api = asana.TasksApi(api_client)
    return tasks_api


def get_stories_api() -> StoriesApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    stories_api = asana.StoriesApi(api_client)
    return stories_api


def get_project_api() -> asana.ProjectsApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    projects_api = asana.ProjectsApi(api_client)
    return projects_api


def get_custom_fields_api() -> asana.CustomFieldsApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    custom_fields_api = asana.CustomFieldsApi(api_client)
    return custom_fields_api


def get_workspace_api() -> asana.WorkspacesApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    workspace_api = asana.WorkspacesApi(api_client)
    return workspace_api


def get_tags_api() -> asana.TagsApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    tags_api = asana.TagsApi(api_client)
    return tags_api


def get_users_api() -> asana.UsersApi:
    # Configure access
    api_client = get_api_client()

    # Create API instance
    users_api = asana.UsersApi(api_client)
    return users_api


def get_api_client() -> ApiClient:
    configuration = asana.Configuration()
    configuration.access_token = PERSONAL_ACCESS_TOKEN
    api_client = asana.ApiClient(configuration)
    return api_client
