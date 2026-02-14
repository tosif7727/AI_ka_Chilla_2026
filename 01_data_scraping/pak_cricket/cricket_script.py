import requests
import pandas as pd

API_KEY = "5c3a4e69-297c-43af-abe6-cf174cf2b956"

url = f"https://api.cricapi.com/v1/players?apikey={API_KEY}&offset=0"

response = requests.get(url)
data = response.json()

players = []

for p in data["data"]:

    if "Pakistan" in str(p):

        players.append({
            "name": p.get("name"),
            "role": p.get("role"),
            "id": p.get("id")
        })

df = pd.DataFrame(players)
df.to_csv("pakistan_players.csv", index=False)

print("Pakistan players saved.")
