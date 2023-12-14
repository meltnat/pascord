import os
from discord import Guild, Intents, Thread, User
from discord.ext.commands import Bot
from pasSetting import PasSetting
from discord.abc import GuildChannel, PrivateChannel


class PasBot(Bot):
    s: PasSetting
    extension_names: list[str]

    def __init__(self, setting: PasSetting) -> None:
        intents = Intents.default()
        intents.message_content = True
        self.s = setting
        super().__init__(intents=intents, command_prefix=self.s.discord.command_prefix)

    async def setup_hook(self) -> None:
        self.load_extensions_folder()
        for name in self.extension_names:
            await self.load_extension(name=name)
        if self.s.debug:
            guild = await self.gf_guild(self.s.discord.guild)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    def load_extensions_folder(self) -> None:
        self.extension_names = []
        path = os.getcwd() + self.s.path.folder.extensions
        list = os.path.dirname(path).split("/")
        name = list[len(list) - 1]
        for node1 in os.listdir(path):
            if os.path.isdir(path + node1):
                for node2 in os.listdir(f"{path}{node1}/"):
                    if os.path.isfile(f"{path}{node1}/{node2}") and node2.endswith(".py"):
                        self.extension_names.append(f"{name}.{node1}.{node2.rstrip('.py')}")
            elif node1.endswith(".py"):
                self.extension_names.append(f"{name}.{node1.rstrip('.py')}")

    async def gf_guild(self, id: int) -> Guild:
        guild = self.get_guild(id)
        if guild is None:
            guild = await self.fetch_guild(id)
        return guild

    async def gf_channel(self, id: int) -> GuildChannel | PrivateChannel | Thread:
        channel = self.get_channel(id)
        if channel is None:
            channel = await self.fetch_channel(id)
        return channel

    async def gf_user(self, id: int) -> User:
        user = self.get_user(id)
        if user is None:
            user = await self.fetch_user(id)
        return user

    async def on_ready(self):
        print(f"login: {self.user.name} [{self.user.id}]")
