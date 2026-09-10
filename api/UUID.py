import requests

def get_uuid(username: str) -> str | None:
     url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
     response = requests.get(url)

     if response.status_code == 200:
         data = response.json()
         return data.get("id")
     else:
         return f"UUID not found, make sure you typed {username} correctly"
