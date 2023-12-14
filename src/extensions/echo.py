from discord import Interaction, app_commands
from discord.ext import commands
from pasbot import PasBot
from pascog import PasCog


class Echo(PasCog):
    @app_commands.command(name="test", description="test")
    @commands.is_owner()
    async def test(self, interaction: Interaction):
        await interaction.response.send_message(self.bot.extensions.__str__(), ephemeral=True)

    @app_commands.command(name="echo", description="echo")
    @app_commands.describe(text="any text")
    async def echo(self, interaction: Interaction, text: str):
        await interaction.response.send_message(text, ephemeral=True)


async def setup(bot: PasBot):
    return await bot.add_cog(Echo(bot))
