import discord
from discord.ext import commands, tasks
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from stream_reader import StreamReader # Helper for ICY metadata

load_dotenv("env.txt")

TOKEN = os.getenv("DISCORD_TOKEN")
VOICE_CH_ID = os.getenv("VOICE_CHANNEL_ID")
STREAM_URL = "https://image2url.com/r2/default/audio/1772379929071-7c44843b-4047-44ce-8473-53b5cb9df981.mp3" 

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- NEW: METADATA FETCHING ---
async def get_stream_title(url):
    try:
        reader = StreamReader()
        stream_data = await reader.get_metadata(url)
        return stream_data.get('title', 'Lofi Radio 24/7')
    except:
        return "Essam Sasa 24/7"

@tasks.loop(seconds=30)
async def update_status():
    await bot.wait_until_ready()
    song_title = await get_stream_title(STREAM_URL)
    
    # Updates the "Listening to..." status
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name=song_title
    )
    await bot.change_presence(activity=activity)

# --- UPDATED RADIO LOOP ---
@tasks.loop(seconds=20)
async def radio_keep_alive():
    await bot.wait_until_ready()
    if not VOICE_CH_ID: return

    try:
        channel = bot.get_channel(int(VOICE_CH_ID))
        vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
        
        if not vc:
            vc = await channel.connect()
        
        if not vc.is_playing():
            if vc.is_connected():
                vc.stop()
            
            source = discord.FFmpegPCMAudio(STREAM_URL, 
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                options='-vn'
            )
            vc.play(discord.PCMVolumeTransformer(source, volume=0.5))
            
    except Exception as e:
        print(f"⚠️ Loop Error: {e}")

# --- STARTUP ---
@bot.event
async def setup_hook():
    # Start both the radio and the status updater
    radio_keep_alive.start()
    update_status.start()
    print("✅ Radio and Status loops active.")

@bot.event
async def on_ready():
    print(f"✅ Active as {bot.user}")

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
