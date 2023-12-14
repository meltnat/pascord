from discord.ext.commands import Cog
from pasbot import PasBot


class PasCog(Cog):
    bot: PasBot

    def __init__(self, bot: PasBot) -> None:
        self.bot = bot
