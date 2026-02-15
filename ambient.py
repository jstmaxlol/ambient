import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import random

TOKEN = ""
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLuI-iSzcTZFUfVlc9OoZL5LbubQ_T_st9"

volume = 0.1

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="::", intents=intents, help_command=None)

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
            source = discord.PCMVolumeTransformer(source, volume=volume)
            vc.play(source)

            while vc.is_playing():
                await asyncio.sleep(1)

@bot.event
async def on_ready():
    print(f"[ambient/status] logged in as {bot.user}")

@bot.command(aliases=['join','hi','gm'])
async def start(ctx):
    global play_task

    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("♥! you have to join a voice channel first~!")
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

    await ctx.send("♥ joined vc, deafened, looping playlist~! 🌫️🎶")

@bot.command(aliases=['quit','bye','gn'])
async def stop(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.disconnect()
        await ctx.send("♥ disconnected.. bye bye~~!")

@bot.command(aliases=['vol'])
async def volume_cmd(ctx, vol: str):
    """set volume in % from 0-100"""
    global volume
    if vol == "?":
        #await ctx.send(f"♥ to set the volume just type `:vol 50%` ~~!")
        await ctx.send(f"♥ the current volume is {round(volume*100)}% ~~!")
        return 1

    try:
        if vol.endswith('%'):
            vol = vol[:-1]
        n = int(vol)
        if n < 0 or n > 100:
            raise ValueError
    except ValueError:
        await ctx.send("♥ volume must be 0-100% ~~")
        return

    volume = n / 100
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_playing() and isinstance(vc.source, discord.PCMVolumeTransformer):
        vc.source.volume = volume

    await ctx.send(f"♥ volume set to {n}% 🌫️")

@bot.command(aliases=['?', 'h'])
async def help(ctx):
    await ctx.send(
        "------------------------------\n"
        "ambient.py --- with ♥ by czjstmax\n"
        "> server: https://discord.gg/6mbgsYveCn\n"
        "> github: https://github.com/jstmaxlol/ambient\n\n"
        "### >> available commands <<\n"
        "`::start` / `::join` / `::hi` / `::gm` - join a vc and use this command to eep ;)\n"
        "`::stop` / `::quit` / `::bye` / `::gn` - exits from the current vc and salutes\n"
        "`::help` / `::?` / `::h` - shows this help/usage message~!\n"
        "------------------------------"
    )

bot.run(TOKEN)

