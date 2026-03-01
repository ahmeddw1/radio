import discord
from discord.ext import commands, tasks
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv("env.txt")

# --- Configuration ---
# Lofi Girl stream (Direct Stream Link)
STREAM_URL = "http://icecast.lofi-girl.com/lofigirl.mp3" 
VOICE_CH_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, status=discord.Status.idle)

FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# --- Dashboard API ---
async def web_server():
    app = web.Application()
    app.router.add_get('/api/dashboard', lambda r: web.json_response({"status": str(bot.status), "latency": f"{bot.latency*1000:.0f}ms"}))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 3000).start()

# --- 24/7 Logic ---
@tasks.loop(seconds=15)
async def check_radio():
    """Background task to ensure bot is in VC and playing 24/7"""
    if not bot.is_ready(): return
    
    channel = bot.get_channel(VOICE_CH_ID)
    if not channel: return

    vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
    
    if not vc:
        vc = await channel.connect()
    
    if not vc.is_playing():
        print("📻 Stream disconnected. Reconnecting...")
        source = discord.FFmpegPCMAudio(STREAM_URL, **FFMPEG_OPTS)
        vc.play(discord.PCMVolumeTransformer(source, volume=0.5))

@bot.event
async def setup_hook():
    # Start web server for dashboard
    asyncio.create_task(web_server())
    # Start 24/7 radio loop
    check_radio.start()
    print("✅ Custom build successful. 24/7 Loop Started.")

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online.")

async def main():
    token = os.getenv("DISCORD_TOKEN")
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
