import discord
import requests
import asyncio
import os
import threading
from flask import Flask
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# -------------------- CONFIG --------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = os.getenv("REGION")
MATCH_REGION = os.getenv("MATCH_REGION")
SUMMONER_NAME = os.getenv("SUMMONER_NAME")
SUMMONER_PUUID = os.getenv("SUMMONER_PUUID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 900))
KD_THRESHOLD = float(os.getenv("KD_THRESHOLD", 0.7))

# -------------------- FLASK WEB SERVER --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.getenv("PORT", 8080))
    print(f"Starting Flask server on port {port}")
    # Disable debug and reloader for production Render deployment
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

print("Starting Flask server thread...")
threading.Thread(target=run_web, daemon=True).start()

# -------------------- DISCORD BOT --------------------
intents = discord.Intents.default()
intents.message_content = True  # Enable this if your bot needs to read message content
bot = commands.Bot(command_prefix="!", intents=intents)

last_match_id = None

# -------------------- RIOT API --------------------
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
    print("Bot ready, starting monitor_matches task...")

    try:
        channel = await bot.fetch_channel(DISCORD_CHANNEL_ID)
        print(f"Fetched channel: {channel}")
    except Exception as e:
        print(f"Failed to fetch channel: {e}")
        return

    while not bot.is_closed():
        try:
            match_id = get_latest_match_id(SUMMONER_PUUID)

            if match_id and match_id != last_match_id:
                print(f"New match detected: {match_id}")
                last_match_id = match_id

                match_data = get_match_details(match_id)
                participant = next(
                    (p for p in match_data['info']['participants'] if p['puuid'] == SUMMONER_PUUID),
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
            print(f"Error in monitor_matches loop: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

# -------------------- BOT EVENTS --------------------
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    bot.loop.create_task(monitor_matches())

# -------------------- START BOT --------------------
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "":
        print("Error: DISCORD_TOKEN is missing or empty.")
    else:
        print("Starting Discord bot...")
        bot.run(DISCORD_TOKEN)
        print("Bot has stopped.")  # This prints only when the bot disconnects
