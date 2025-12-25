from typing import List

from asana import StoriesApi

from apify.skip_trace.owner_data import PropertyOwnerInfo
from my_asana.authenticate import get_stories_api, get_tasks_api
from my_asana.users import Users


def tag_user_in_comment(user_id: str) -> str:
    return f'<a data-asana-gid="{user_id}"/>'


def add_comment_to_task(task_id: str, comment: str):
    stories_api: StoriesApi = get_stories_api()

    body = {
        "data": {
            "html_text": comment
        }
    }
    opts = {
        'opt_fields': "html_text"
    }

    stories_api.create_story_for_task(
        task_gid=task_id,
        body=body,
        opts=opts
    )


def add_followers_to_task(task_id: str):
    body = {
        "data": {
            "followers": [user.user_id for user in [Users.ORI, Users.ITAMAR, Users.HILA]]
        }
    }
    opts = {}

    get_tasks_api().add_followers_for_task(body, task_id, opts)


def get_up_for_sale_again_message() -> str:
    users_str: str = "".join([tag_user_in_comment(user.user_id) for user in [Users.ORI, Users.ITAMAR, Users.HILA]])
    main_message: str = 'This property failed in contingency. It is now back on the market! Please review it.'
    html_text: str = f'<body>{users_str}\n{main_message}</body>'
    return html_text


def get_property_sold_message() -> str:
    users_str: str = "".join([tag_user_in_comment(user.user_id) for user in [Users.ORI, Users.ITAMAR, Users.HILA]])
    main_message: str = 'This property is now sold. Moving it to Decline.'
    html_text: str = f'<body>{users_str}\n{main_message}</body>'
    return html_text


def get_property_for_rent_message() -> str:
    main_message: str = 'This property is now for rent. Moving it to Decline.'
    html_text: str = f'<body>{main_message}</body>'
    return html_text

def get_off_market_message() -> str:
    main_message: str = 'This property is now off-market. Moving it to Listing Expired (Matt\'s Initiative).'
    html_text: str = f'<body>{main_message}</body>'
    return html_text


def get_full_owner_details_message(owner: PropertyOwnerInfo) -> str:
    phones_str = "\n".join(
        [f"- {p.number} ({p.type}, last reported {p.last_reported_date})" for p in owner.phone_numbers]
    )
    relatives_str = "\n".join(
        [f"- {relative.name} (age {relative.age})" for relative in owner.relatives]
     ) if owner.relatives else "None listed"

    main_message: str = (
        f"👤 **Owner Info**\n"
        f"Name: {owner.first_name} {owner.last_name} (Age {owner.age})\n"
        f"Lives in: {owner.lives_in_address}\n"
        f"Person Link: {owner.person_link}\n"
        f"📞 **Phones:**\n{phones_str or 'No phones listed'}\n"
        f"✉️ **Email:** {owner.email or 'None'}\n"
        f"👪 **Relatives:**\n{relatives_str}"
    )

    html_text: str = f'<body>{main_message}</body>'
    return html_text