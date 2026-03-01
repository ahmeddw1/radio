import discord
from discord.ext import commands, tasks
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv

# Try to load from file, but don't crash if it's missing
load_dotenv("env.txt")

# --- 1. CONFIGURATION ---
# We pull these from Railway Environment Variables
TOKEN = os.getenv("DISCORD_TOKEN")
VOICE_CH_ID = os.getenv("VOICE_CHANNEL_ID")
STREAM_URL = "http://icecast.lofi-girl.com/lofigirl.mp3" 

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix="!", 
    intents=intents, 
    status=discord.Status.idle,
    activity=discord.Activity(type=discord.ActivityType.listening, name="🎧 Lofi 24/7")
)

FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# --- 2. 24/7 RADIO LOOP ---
@tasks.loop(seconds=20)
async def radio_keep_alive():
    if not bot.is_ready() or not VOICE_CH_ID:
        return

    try:
        channel = bot.get_channel(int(VOICE_CH_ID))
        if not channel:
            print(f"❌ Could not find channel ID: {VOICE_CH_ID}")
            return

        vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
        
        if not vc:
            vc = await channel.connect()
        
        if not vc.is_playing():
            print("📻 Restarting Lofi stream...")
            source = discord.FFmpegPCMAudio(STREAM_URL, **FFMPEG_OPTS)
            vc.play(discord.PCMVolumeTransformer(source, volume=0.5))
    except Exception as e:
        print(f"⚠️ Loop Error: {e}")

# --- 3. DASHBOARD API ---
async def web_server():
    app = web.Application()
    # Simple check for your dashboard
    app.router.add_get('/api/dashboard', lambda r: web.json_response({
        "status": str(bot.status),
        "latency": f"{bot.latency*1000:.0f}ms",
        "playing": True
    }))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 3000).start()

# --- 4. STARTUP ---
@bot.event
async def setup_hook():
    asyncio.create_task(web_server())
    radio_keep_alive.start()
    print("✅ Dashboard API and Radio Loop initialized.")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def main():
    if not TOKEN:
        print("\n" + "!"*40)
        print("CRITICAL ERROR: DISCORD_TOKEN IS MISSING!")
        print("Please go to Railway -> Variables and add 'DISCORD_TOKEN'")
        print("!"*40 + "\n")
        return

    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
