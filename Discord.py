import discord
import os
from collections import deque
from discord.ext import commands
from discord.utils import get
import yt_dlp as youtube_dl
from webserver import keep_alive

# Inicializar bot y configuraciones
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
playlist = deque()

# ---------------------------- BOT EVENTS ----------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="/help")
    )
    await bot.tree.sync()
    keep_alive()  # Activar servidor web para Render

# ---------------------------- SLASH COMMANDS ----------------------------
@bot.tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎵 Music Bot Commands",
        description="**List of commands:**\n",
        color=discord.Color.blue()
    )
    
    # Comandos de voz
    embed.add_field(
        name="🎧 Voice Control",
        value=(
            "`/connect` - Join the bot to your voice channel\n"
            "`/disconnect` - Disconnect the bot\n"
        ),
        inline=False
    )
    
    # Comandos de música
    embed.add_field(
        name="🎶 Music Controls",
        value=(
            "`/play [query/url]` - Play from YouTube/Spotify\n"
            "`/skip` - Skip current song\n"
            "`/pause` - Pause playback\n"
            "`/resume` - Resume playback\n"
            "`/queue` - Show current queue\n"
        ),
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="connect", description="Connect the bot to your voice channel")
async def connect(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    channel = interaction.user.voice.channel

    if not channel:
        embed = discord.Embed(
            title="Error",
            description="❌ You must be in a voice channel!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    playlist.clear()
    embed = discord.Embed(
        title="Connected",
        description="🎶 Bot joined the voice channel.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="disconnect", description="Disconnect the bot")
async def disconnect(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_connected():
        await voice.disconnect()
        embed = discord.Embed(
            title="Disconnected",
            description="🎶 Bot left the voice channel.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="Error",
            description="⚠️ Bot is not connected!",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="play", description="Play a song from YouTube/Spotify")
async def play(interaction: discord.Interaction, input: str):
    from Youtube import play as yt_play, search_youtube  # <-- ¡Solo importa search_youtube!
    
    try:
        if not interaction.user.voice:
            embed = discord.Embed(
                title="❌ Error",
                description="Join a voice channel first!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        # Usar SOLO search_youtube (maneja URLs y búsquedas)
        title, url = await search_youtube(input)

        if url:
            await yt_play(interaction, bot, url, title)
            embed = discord.Embed(
                title="🎶 Song Added",
                description=f"**{title}** added to the queue.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ Error",
                description="No results found.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description="Failed to play the song.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        print(f"Error: {e}")

@bot.tree.command(name="queue", description="Show the current queue")
async def queue(interaction: discord.Interaction):
    from Controls import show_queue
    await show_queue(interaction)

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    from Controls import skip_song
    await skip_song(interaction)

@bot.tree.command(name="pause", description="Pause the playback")
async def pause(interaction: discord.Interaction):
    from Controls import pause_music
    await pause_music(interaction)

@bot.tree.command(name="resume", description="Resume the playback")
async def resume(interaction: discord.Interaction):
    from Controls import resume_music
    await resume_music(interaction)

# ---------------------------- EJECUCIÓN ----------------------------
if __name__ == "__main__":
    keep_alive()  # Iniciar servidor web
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))  # Token desde variables de entorno
