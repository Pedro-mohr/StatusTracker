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
            title="❌ Error",
            description="You are not in a voice channel.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)  # Usar followup, no response
        return

    voice = get(bot.voice_clients, guild=interaction.guild)
    if not voice or not voice.is_connected():
        voice = await channel.connect()

    # Obtener título con API de YouTube
    try:
        video_id = url.split("v=")[-1].split("&")[0]
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if not response["items"]:
            embed = discord.Embed(
                title="⚠️ Error",
                description="Invalid YouTube URL.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
            return

        title = response["items"][0]["snippet"]["title"]

    except (IndexError, HttpError):
        # Fallback a yt-dlp para URLs complejas
        with youtube_dl.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info["title"]

   # Añadir a la playlist con embed
    if track_name:
        playlist.append((track_name, url))
        embed = discord.Embed(
            title="🎶 Song Added",
            description=f"**{track_name}** added to the queue.",
            color=discord.Color.green()
        )
    else:
        playlist.append((title, url))
        embed = discord.Embed(
            title="🎶 Song Added",
            description=f"**{title}** added to the queue.",
            color=discord.Color.green()
        )

    await interaction.followup.send(embed=embed)  # Enviar como followup

    if not voice.is_playing():
        await play_next(interaction, voice)

async def play_next(interaction, voice):
    global playlist
    if playlist:
        title, url = playlist.popleft()

        # Extraer stream de audio
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info["url"]
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to process the video.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            print(f"Stream Error: {e}")
            return

        # Reproducir
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

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{title}**",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="🎶 Queue Empty",
            description="The playlist has ended.",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)

async def search_youtube(query: str):
    """Busca un video en YouTube usando la API oficial."""
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
        print(f"🔴 YouTube API Error: {e}")
        return None, None
