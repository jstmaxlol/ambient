import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

TOKEN = ""
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLuI-iSzcTZFUfVlc9OoZL5LbubQ_T_st9"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=";;", intents=intents)

ytdl_playlist_opts = {
    "quiet": True,
    "extract_flat": True,
}

ytdl_audio_opts = {
    "quiet": True,
    "format": "bestaudio/best",
}

ffmpeg_opts = {
    "options": "-vn",
}

playlist_urls = []
play_task = None

def load_playlist():
    global playlist_urls
    with yt_dlp.YoutubeDL(ytdl_playlist_opts) as ydl:
        info = ydl.extract_info(PLAYLIST_URL, download=False)
        playlist_urls = [entry["url"] for entry in info["entries"]]
    random.shuffle(playlist_urls)

async def play_loop(vc: discord.VoiceClient):
    global playlist_urls

    while True:
        for url in playlist_urls:
            if not vc.is_connected():
                return

            with yt_dlp.YoutubeDL(ytdl_audio_opts) as ydl:
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
    global play_task

    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("join a voice channel first")
        return

    channel = ctx.author.voice.channel

    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.move_to(channel)
    else:
        vc = await channel.connect()

    await ctx.guild.change_voice_state(
        channel=vc.channel,
        self_deaf=True
    )


    if not playlist_urls:
        load_playlist()

    if play_task and not play_task.done():
        play_task.cancel()

    play_task = bot.loop.create_task(play_loop(vc))

    await ctx.send("joined vc, deafened, looping playlist 🌫️🎶")

@bot.command()
async def stop(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.disconnect()
        await ctx.send("disconnected")

bot.run(TOKEN)

