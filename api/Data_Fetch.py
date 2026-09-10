# Module imports
import os
import requests
from dotenv import load_dotenv

# Custom function imports
from UUID import get_uuid

# Set Base and Env file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "api.env"))

print("Looking for env file at:", ENV_PATH)  # Debug line
print("File exists?:", os.path.exists(ENV_PATH))  # Debug line

# Load environment variables from api.env file
load_dotenv(dotenv_path=ENV_PATH)

# Global API Key
API_KEY = os.getenv("HYPIXEL_API_KEY")


# --- HYPIXEL API REQUESTS ---
def get_sb_profiles(player_uuid: str, api_key: str) -> dict | None:
    url = "https://api.hypixel.net/v2/skyblock/profiles"
    headers = {"API-Key": api_key}
    params = {"uuid": player_uuid}

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    return None


# Test execution script
if __name__ == "__main__":
    username = input("Enter your username: ")
    user_uuid = get_uuid(username)

    if user_uuid and API_KEY:
        data = get_sb_profiles(user_uuid, API_KEY)
        print(data)
    else:
        print(f"Error: Missing UUID ({user_uuid}) or API_KEY ({API_KEY})!")