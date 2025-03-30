from discord.utils import get
from collections import deque
import yt_dlp as youtube_dl
import discord
import os
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") 
playlist = deque()

async def play(interaction, bot, url, track_name=None):
    global playlist
    channel = interaction.user.voice.channel
    if not channel:
        embed = discord.Embed(
            title="Error",
            description="❌ You are not in a voice channel.",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed)
        return

    voice = get(bot.voice_clients, guild=interaction.guild)
    if not voice or not voice.is_connected():
        voice = await channel.connect()

    ydl_opts = {"format": "bestaudio/best", "noplaylist": "True", "quiet": True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info["title"]

    if track_name:
        playlist.append((track_name, url))
        await interaction.followup.send(f"🎶 Added **{track_name}** to the queue.")
    else:
        playlist.append((title, url))
        await interaction.followup.send(f"🎶 Added **{title}** to the queue.")

    if not voice.is_playing():
        await play_next(interaction, voice)

async def search_youtube(query):
    options = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    with youtube_dl.YoutubeDL(options) as ydl:
        try:
            results = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"]
            if results:
                return results[0]["title"], results[0]["url"]
        except Exception as e:
            print(f"Search error: {e}")
            return None, None

async def search_query(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(part="snippet", maxResults=1, q=query, type="video")
    response = request.execute()
    if response["items"]:
        video_id = response["items"][0]["id"]["videoId"]
        title = response["items"][0]["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        return title, url
    else:
        return None, None

async def play_next(interaction, voice):
    global playlist
    if playlist:
        title, url = playlist.popleft()

        ydl_opts = {"format": "bestaudio/best", "noplaylist": "True", "quiet": True}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info["url"]

        ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_opts)
        voice.play(
            audio_source,
            after=lambda e: interaction.client.loop.create_task(play_next(interaction, voice)),
        )
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.10

        await interaction.followup.send(f"🎶 Now playing **{title}**.")
    else:
        await interaction.followup.send("🎶 The queue is empty.")