import discord
import requests
import asyncio
import os

from discord.ext import commands
import config 

# -------------------- CONFIG --------------------
DISCORD_TOKEN = config.DISCORD_TOKEN
DISCORD_CHANNEL_ID = config.DISCORD_CHANNEL_ID

RIOT_API_KEY = config.RIOT_API_KEY
REGION = config.REGION
MATCH_REGION = config.MATCH_REGION

SUMMONER_NAME = config.SUMMONER_NAME

CHECK_INTERVAL = config.CHECK_INTERVAL
KD_THRESHOLD = config.KD_THRESHOLD

# -------------------- DISCORD BOT --------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Global state to remember last match
last_match_id = None

# -------------------- RIOT API --------------------
def get_summoner_data():
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{SUMMONER_NAME}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

def get_latest_match_id(puuid):
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    match_ids = response.json()
    return match_ids[0] if match_ids else None

def get_match_details(match_id):
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

def calculate_kd(kills, deaths):
    return kills / deaths if deaths > 0 else kills

# -------------------- MONITOR TASK --------------------
async def monitor_matches():
    global last_match_id
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    puuid = config.SUMMONER_PUUID

    while not bot.is_closed():
        try:
            match_id = get_latest_match_id(puuid)

            if match_id and match_id != last_match_id:
                print(f"New match detected: {match_id}")
                last_match_id = match_id

                match_data = get_match_details(match_id)
                participant = next(
                    (p for p in match_data['info']['participants'] if p['puuid'] == puuid),
                    None
                )

                if participant:
                    kills = participant['kills']
                    deaths = participant['deaths']
                    kd = calculate_kd(kills, deaths)

                    print(f"K/D: {kills}/{deaths} = {kd:.2f}")

                    if kd < KD_THRESHOLD:
                        await channel.send(
                            f"⚠️ **{SUMMONER_NAME}** had a rough game!\n"
                            f"**K/D Ratio:** {kills}/{deaths} = {kd:.2f} 😬"
                        )

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

# -------------------- START BOT --------------------
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    # Start the monitor task when the bot is ready
    bot.loop.create_task(monitor_matches())

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
