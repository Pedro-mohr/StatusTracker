from discord.utils import get
from collections import deque
import yt_dlp as youtube_dl
import discord
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

    # Obtener título usando la API de YouTube (evitar yt-dlp para metadata)
    try:
        video_id = url.split("v=")[-1].split("&")[0]  # Extraer ID de URL
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if not response["items"]:
            await interaction.followup.send("⚠️ Invalid YouTube URL.")
            return

        title = response["items"][0]["snippet"]["title"]

    except (IndexError, HttpError):
        # Fallback a yt-dlp solo para URLs complejas
        with youtube_dl.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info["title"]

    # Añadir a la playlist
    if track_name:
        playlist.append((track_name, url))
        await interaction.followup.send(f"🎶 Added **{track_name}** to the queue.")
    else:
        playlist.append((title, url))
        await interaction.followup.send(f"🎶 Added **{title}** to the queue.")

    if not voice.is_playing():
        await play_next(interaction, voice)

async def search_youtube(query):
    """Búsqueda usando la API oficial de YouTube (sin yt-dlp)"""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=1
        )
        response = request.execute()
        
        if not response["items"]:
            return None, None

        video_id = response["items"][0]["id"]["videoId"]
        title = response["items"][0]["snippet"]["title"]
        return title, f"https://youtu.be/{video_id}"

    except HttpError as e:
        print(f"YouTube API Error: {e}")
        return None, None

async def play_next(interaction, voice):
    global playlist
    if playlist:
        title, url = playlist.popleft()

        # Usar yt-dlp SOLO para extraer el stream de audio
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info["url"]
        except Exception as e:
            await interaction.followup.send("❌ Failed to process the video.")
            print(f"Stream Error: {e}")
            return

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
