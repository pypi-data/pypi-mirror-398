
import requests

url = "https://app.realie.ai/api/public/property/address/"

querystring = {
    "limit":"10",
    "state": "PA",
    "address": "152 W Patty Ln"
}

headers = {"Authorization": "8193a587690fe842213f0248a8ae0deb"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())