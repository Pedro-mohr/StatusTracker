# pip install -r requirements.txt

import discord
from discord.ext import commands
from discord import app_commands
import os
import yt_dlp as youtube_dl
import asyncio
import openai
from dotenv import load_dotenv
from collections import deque
import webserver

# Configuración inicial
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ------------------------- Música -------------------------
class MusicQueue:
    def __init__(self):
        self.queue = deque()
        self.now_playing = None

    def add(self, track: str):
        self.queue.append(track)
    
    def skip(self):
        if self.queue:
            self.now_playing = self.queue.popleft()
            return self.now_playing
        return None

music_queues = {}

def get_queue(guild_id: int) -> MusicQueue:
    if guild_id not in music_queues:
        music_queues[guild_id] = MusicQueue()
    return music_queues[guild_id]

# Configuración yt-dlp
ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'cookiefile': 'cookies.txt',
    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
}

ffmpeg_options = {'options': '-vn -loglevel error'}
ytdl = youtube_dl.YoutubeDL(ytdl_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, data, volume=0.5):
        super().__init__(source, volume)
        self.title = data.get('title', 'Unknown track')

    @classmethod
    async def from_url(cls, url):
        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data)

# ------------------------- Comandos -------------------------
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="/help"))

@bot.tree.command(name="play", description="Play music from YouTube")
@app_commands.describe(url="YouTube URL or search query")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("❌ You must be in a voice channel!")
    
    try:
        voice = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
        player = await YTDLSource.from_url(url)
        get_queue(interaction.guild.id).add(player)
        
        if not voice.is_playing():
            await play_next(interaction.guild)
        await interaction.followup.send("✅ Added to queue")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

async def play_next(guild):
    queue = get_queue(guild.id)
    voice = guild.voice_client
    if voice and not voice.is_playing():
        next_track = queue.skip()
        if next_track:
            voice.play(next_track, after=lambda e: bot.loop.create_task(play_next(guild)))

@bot.tree.command(name="skip", description="Skip current track")
async def skip(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_playing():
        voice.stop()
        await interaction.response.send_message("⏭ Skipped track")
    else:
        await interaction.response.send_message("❌ Nothing is playing", ephemeral=True)

@bot.tree.command(name="stop", description="Stop music and disconnect")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        music_queues.pop(interaction.guild.id, None)
        await interaction.response.send_message("⏹ Music stopped")
    else:
        await interaction.response.send_message("❌ Bot is not in a channel", ephemeral=True)

@bot.tree.command(name="translate", description="Translate text with AI")
@app_commands.describe(text="Text to translate", language="Target language")
@app_commands.choices(language=[
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Spanish", value="es")
])
async def translate(interaction: discord.Interaction, text: str, language: app_commands.Choice[str]):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": f"Translate to {language.name} professionally"
            },{
                "role": "user",
                "content": text
            }]
        )
        await interaction.response.send_message(f"🌍 **Translation ({language.name}):**\n{response.choices[0].message.content}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="hello", description="Get a greeting from the bot")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("👋 Hello! I'm ready to play music and translate text!")

@bot.tree.command(name="info", description="Show bot information")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Information",
        description="Professional Discord bot with music and translation features",
        color=0x00ff00
    )
    embed.add_field(name="Commands", value="/play, /skip, /stop, /translate, /hello, /info", inline=False)
    await interaction.response.send_message(embed=embed)

# ------------------------- Inicio -------------------------
if __name__ == "__main__":
    webserver.keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))