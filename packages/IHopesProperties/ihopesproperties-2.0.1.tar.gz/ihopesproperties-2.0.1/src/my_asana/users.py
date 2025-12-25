import requests
from my_asana.consts import PERSONAL_ACCESS_TOKEN
from enum import Enum

def get_users():
    url = "https://app.asana.com/api/1.0/users"
    headers = {
        "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        print(f"Error fetching users: {response.status_code} - {response.text}")
        return []

#users = get_users()
#print(users)  # This will give you a list of users and their IDs

class Users(Enum):
    ITAMAR = 'Itamar Halevi', '1206867055887039'
    ORI = 'Ori Peri', '1206866397949967'
    HILA = 'Hila Lichtman Peri', '1207911884233138'
    U25TO40 = '25 to 40', '1207911699123552'

    def __init__(self, user_name: str, user_id: str) -> None:
        self.user_name: str = user_name
        self.user_id: str = user_id 


def randomly_select_user_id() -> str:
    import random
    # Create a list of user IDs excluding U25TO40
    user_ids = [user.user_id for user in Users if user in [Users.ITAMAR, Users.ORI]]

    # Select a random user ID from the filtered list
    selected_user_id = random.choice(user_ids)

    return selected_user_id
