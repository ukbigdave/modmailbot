import datetime
import discord
from discord import app_commands
from discord.ext import commands
from raidView import RaidView


class Bot(commands.Bot):
    def __init__(self, *, command_prefix: str, intents: discord.Intents) -> None:
        super().__init__(command_prefix=command_prefix, intents=intents)

    async def setup_hook(self) -> None:
        for guild in self.guilds:
            print(f"In guilds: {guild.id}")
            self.tree.copy_global_to(guild=discord.Object(id=guild.id))
            await self.tree.sync(guild=discord.Object(id=guild.id))


intents = discord.Intents.all()
bot = Bot(command_prefix="!", intents=intents)


@bot.tree.error
async def on_error(interaction: discord.Interaction, e: Exception) -> None:
    print(e)
    if isinstance(e, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"This command is on cooldown for **{round(e.retry_after, 1)}** more seconds.", ephemeral=True)


@bot.event
async def on_ready() -> None:
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")

    await bot.setup_hook()

    return


@bot.tree.command(name="raid", description="Start a new raid")
@app_commands.describe(boss_name="Name of boss of this raid", trainer_code="Trainer code of the raid leader", number_of_members="Maximum number of members in the raid (default: 5)")
@app_commands.checks.cooldown(1, 5, key=lambda interaction: interaction.channel_id)
async def raid(interaction: discord.Interaction, boss_name: str, trainer_code: str, number_of_members: int = None) -> None:
    if len(boss_name.split()) > 2:
        await interaction.response.send_message("The boss name must be one or two words.", ephemeral=True)
        return

    trainer_code = trainer_code.replace(" ", "")

    if len(trainer_code) != 12:
        await interaction.response.send_message("The trainer code must be 12 digits long.", ephemeral=True)
        return

    try:
        int(trainer_code)
    except ValueError:
        await interaction.response.send_message("The trainer code must be 12 digits long.", ephemeral=True)
        return

    if number_of_members is None:
        number_of_members = 5

    if number_of_members > 10:
        await interaction.response.send_message("The maximum number of additional members in a raid is 10.", ephemeral=True)
        return

    if number_of_members < 1:
        await interaction.response.send_message("The minimum number of additional members in a raid is 1.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Raid", description=f"**{boss_name}**\n**{trainer_code}**", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(
        name="Host", value=f"{interaction.user.mention}", inline=False)
    embed.add_field(
        name=f"Participants 0/{number_of_members}", value="None", inline=False)
    embed.set_footer(text="Press the button below to join this raid.")
    embed.set_thumbnail(
        url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
    await interaction.response.send_message(content=trainer_code, embed=embed)
    message = await interaction.original_response()
    view = RaidView(interaction.user, message, embed, None, None, None)
    await message.edit(view=view)

file = open("token.txt", "r")
TOKEN = file.readline()
file.close()
bot.run(TOKEN)
