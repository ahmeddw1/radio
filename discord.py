import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv

load_dotenv("env.txt")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Lofi Girl YouTube stream or any direct MP3 stream
# Replace with your preferred 24/7 stream URL
LOFI_STREAM_URL = "https://play.streamaudio.de/lofi" 

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    # Start the 24/7 check loop
    keep_alive_radio.start()

@tasks.loop(seconds=20)
async def keep_alive_radio():
    """Ensures the bot is always in the channel and playing."""
    channel_id = int(os.getenv("VOICE_CHANNEL_ID"))
    channel = bot.get_channel(channel_id)
    
    if not channel:
        return

    # Check if bot is connected
    vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
    
    if not vc:
        vc = await channel.connect()
    
    if not vc.is_playing():
        print("📻 Radio stopped or disconnected. Restarting stream...")
        vc.stop()
        source = discord.FFmpegPCMAudio(LOFI_STREAM_URL, **FFMPEG_OPTIONS)
        vc.play(discord.PCMVolumeTransformer(source, volume=0.5))

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
