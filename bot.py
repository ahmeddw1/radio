import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio

# --- CONFIG ---
# Standard YDL options for high-quality audio streaming
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0' # Prevents IPv6 issues
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.command(name="play")
async def play(ctx, *, search: str = None):
    """Plays a stream URL or searches YouTube for a song name."""
    if not ctx.author.voice:
        return await ctx.send("❌ You need to be in a voice channel!")

    # If no search term provided, fall back to your default radio stream
    if search is None:
        url = STREAM_URL
        title = "24/7 Radio Stream"
    else:
        await ctx.send(f"🔍 Searching for `{search}`...")
        
        # Use yt-dlp to find the video
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url = info['url']
                title = info['title']
            except Exception as e:
                return await ctx.send(f"❌ Could not find that song: {e}")

    # Connect logic
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not vc:
        vc = await ctx.author.voice.channel.connect()
    
    if vc.is_playing():
        vc.stop()

    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
    vc.play(discord.PCMVolumeTransformer(source, volume=0.5))
    
    await ctx.send(f"🎶 Now playing: **{title}**")
    # Change status so the 24/7 loop doesn't override your custom song immediately
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=title))

@bot.command(name="stop")
async def stop(ctx):
    """Stops the music and disconnects."""
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc:
        await vc.disconnect()
        await ctx.send("⏹️ Stopped and disconnected.")
    else:
        await ctx.send("❌ I'm not in a voice channel.")
