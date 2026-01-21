import discord
from discord.ext import commands
import yt_dlp
import asyncio

TOKEN = ""                  # bot token
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLuI-iSzcTZFUfVlc9OoZL5LbubQ_T_st9"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": True,
}

ffmpeg_opts = {
    "options": "-vn"
}

playlist_urls = []

def load_playlist():
    global playlist_urls
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(PLAYLIST_URL, download=False)
        playlist_urls = [entry["url"] for entry in info["entries"]]

async def play_loop(vc):
    global playlist_urls
    while True:
        for url in playlist_urls:
            with yt_dlp.YoutubeDL({"format": "bestaudio"}) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info["url"]

            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_opts)
            vc.play(source)

            while vc.is_playing():
                await asyncio.sleep(1)

@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")

@bot.command()
async def start(ctx):
    if not ctx.author.voice:
        await ctx.send("join a voice channel first")
        return

    channel = ctx.author.voice.channel
    vc = await channel.connect()

    load_playlist()
    await play_loop(vc)

bot.run(TOKEN)

