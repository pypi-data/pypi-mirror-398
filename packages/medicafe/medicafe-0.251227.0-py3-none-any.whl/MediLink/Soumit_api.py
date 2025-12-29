import os
import requests
from icecream import ic
from dotenv import load_dotenv

load_dotenv()

url = "https://api.availity.com/availity/development-partner/v1/token"

data = {
    'grant_type': 'client_credentials',
    'client_id': os.getenv("CLIENT_ID"),
    'client_secret': os.getenv("CLIENT_SECRET"),
    'scope': 'hipaa'
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

resp = requests.post(url, headers = headers, data = data)
ic(resp.json())