from Youtube import playlist

async def show_queue(interaction):
    if playlist:
        description = "\n".join([f"**{i+1}.** {title}" for i, (title, _) in enumerate(playlist)])
        embed = discord.Embed(
            title="🎵 Current Queue",
            description=description,
            color=discord.Color.gold(),
        )
    else:
        embed = discord.Embed(
            title="Empty Queue",
            description="🎶 The queue is empty.",
            color=discord.Color.blue(),
        )
    await interaction.response.send_message(embed=embed)

async def clear_queue(interaction):
    playlist.clear()
    embed = discord.Embed(
        title="Queue Cleared",
        description="🗑️ Playlist has been cleared.",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed)