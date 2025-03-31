import discord
import os
from collections import deque
from discord.ext import commands
from discord.utils import get
from webserver import keep_alive

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
playlist = deque()

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="/help")
    )
    await bot.tree.sync()
    keep_alive()

@bot.tree.command(name="help", description="Show all commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎵 Bot Commands",
        description="**Available commands:**\n",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🎧 Voice",
        value=(
            "`/connect` - Join voice channel\n"
            "`/disconnect` - Leave voice channel\n"
        ),
        inline=False
    )
    embed.add_field(
        name="🎶 Music",
        value=(
            "`/play [query/url]` - Play music\n"
            "`/skip` - Skip song\n"
            "`/pause` - Pause\n"
            "`/resume` - Resume\n"
            "`/queue` - Show queue\n"
        ),
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="connect", description="Join voice channel")
async def connect(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    channel = interaction.user.voice.channel

    if not channel:
        embed = discord.Embed(
            title="❌ Error",
            description="Join a voice channel first!",
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
        title="✅ Connected",
        description="Bot joined the voice channel.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="play", description="Play a song")
async def play(interaction: discord.Interaction, input: str):
    from Youtube import play as yt_play, search_youtube
    
    await interaction.response.defer()  # Línea crítica
    
    try:
        if not interaction.user.voice:
            embed = discord.Embed(
                title="❌ Error",
                description="Join a voice channel first!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)  # Usar followup
            return

        title, url = await search_youtube(input)

        if url:
            await yt_play(interaction, bot, url, title)
            embed = discord.Embed(
                title="🎶 Song Added",
                description=f"**{title}** added to the queue.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ Error",
                description="No results found.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title="❌ Critical Error",
            description="Check logs for details.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        print(f"Error: {e}")

@bot.tree.command(name="queue", description="Show queue")
async def queue(interaction: discord.Interaction):
    from Youtube import playlist
    if not playlist:
        embed = discord.Embed(
            title="🎶 Queue",
            description="The queue is empty.",
            color=discord.Color.gold()
        )
    else:
        songs = "\n".join([f"**{i+1}.** {title}" for i, (title, _) in enumerate(playlist)])
        embed = discord.Embed(
            title="🎵 Current Queue",
            description=songs,
            color=discord.Color.blue()
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="skip", description="Skip current song")
async def skip(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.stop()
        embed = discord.Embed(
            title="⏭️ Skipped",
            description="Current song skipped.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Error",
            description="No music is playing.",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pause", description="Pause music")
async def pause(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.pause()
        embed = discord.Embed(
            title="⏸️ Paused",
            description="Playback paused.",
            color=discord.Color.orange()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Error",
            description="No music is playing.",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="resume", description="Resume music")
async def resume(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_paused():
        voice.resume()
        embed = discord.Embed(
            title="▶️ Resumed",
            description="Playback resumed.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Error",
            description="No music is paused.",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="disconnect", description="Disconnect bot")
async def disconnect(interaction: discord.Interaction):
    voice = get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_connected():
        await voice.disconnect()
        embed = discord.Embed(
            title="✅ Disconnected",
            description="Bot left the voice channel.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Error",
            description="Bot is not connected!",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
