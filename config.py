import os

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
RIOT_API_KEY = os.environ["RIOT_API_KEY"]
REGION = os.environ.get("REGION", "na1")
MATCH_REGION = os.environ.get("MATCH_REGION", "americas")
SUMMONER_NAME = os.environ["SUMMONER_NAME"]
SUMMONER_PUUID = os.environ["SUMMONER_PUUID"]
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 900))
KD_THRESHOLD = float(os.environ.get("KD_THRESHOLD", 0.7))