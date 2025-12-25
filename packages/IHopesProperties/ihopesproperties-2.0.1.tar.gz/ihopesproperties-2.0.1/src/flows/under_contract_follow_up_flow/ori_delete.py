from asana import CustomFieldsApi, TagsApi, UsersApi

from my_asana.authenticate import get_project_api, get_custom_fields_api, get_workspace_api, get_tags_api, get_users_api
#
# users_api: UsersApi = get_users_api()
# list(users_api.get_users(opts={'workspace':WORKSPACE_ID}))
#
#
#
# projects_api = get_project_api()
# projects_api.get_project(REAL_ESTATE_LEADS_PROJECT_ID, {"opt_fields": "custom_fields"})
#
# tags_api: TagsApi = get_tags_api()
# #list(tags_api.get_tags(opts={}))
#
# list(tags_api.get_tags(opts={'workspace':WORKSPACE_ID}))
# print(tags_api.get_tags_for_workspace(LEADS_PROJECT_ID))


#workspace_api = get_workspace_api()

#workspaces = workspace_api.get_workspaces()

# for workspace in workspaces.data:
#     print(f"Workspace ID: {workspace.gid} - Name: {workspace.name}")


# projects_api = get_project_api()
# project_id = LEADS_PROJECT_ID
#
# project = projects_api.get_project(project_id, {"opt_fields": "custom_fields"})
# for field in project.data["custom_fields"]:
#     print(field["gid"], field["name"])
#
# custom_fields_api = get_custom_fields_api()
# priority_field = custom_fields_api.get_custom_field(priority_field_id)
# for option in priority_field.enum_options:
#     print(option.gid, option.name)
