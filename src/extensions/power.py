import os
import sys
import discord
from discord.interactions import Interaction
from pasbot import PasBot
from pascog import PasCog
from discord import Interaction, app_commands, ui


def is_owner():
    def predicate(interaction: Interaction) -> bool:
        return interaction.client.is_owner(interaction.user)

    return app_commands.check(predicate=predicate)


class ExtensionReloadList(ui.Select):
    bot: PasBot

    def __init__(self, bot: PasBot):
        self.bot = bot
        super().__init__(options=[discord.SelectOption(label=i) for i in self.bot.extension_names])

    async def callback(self, interaction: Interaction):
        module = self.bot.extensions.get(self.values[0])
        if module is None:
            list = os.path.dirname(self.bot.s.path.folder.extensions).split("/")
            name = list[len(list) - 1]
            module = self.bot.extensions.get(f"{name}.{self.values[0]}")
        if module is None:
            await interaction.response.send_message(f"{self.values[0]} is not exist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Reloading {module.__name__} ...", ephemeral=True)
            await self.bot.reload_extension(name=module.__name__, package=module.__package__)
            log = await interaction.original_response()
            await log.edit(content=log.content + "\nDone")


class ExtensionReloadView(ui.View):
    def __init__(self, bot: PasBot):
        super().__init__(timeout=30)
        self.add_item(ExtensionReloadList(bot=bot))


class Power(PasCog):
    @app_commands.command(name="ereload", description="Extensionを再読み込みします")
    @app_commands.describe(target="Target Extension")
    @is_owner()
    async def extension_reload(self, interaction: Interaction, target: str = None):
        if target is None:
            await interaction.response.send_message(view=ExtensionReloadView(self.bot), ephemeral=True)
            return
        module = self.bot.extensions.get(target)
        if module is None:
            list = os.path.dirname(self.bot.s.path.folder.extensions).split("/")
            name = list[len(list) - 1]
            module = self.bot.extensions.get(f"{name}.{target}")
        if module is None:
            await interaction.response.send_message(f"{target} is not exist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Reloading {module.__name__} ...", ephemeral=True)
            await self.bot.reload_extension(name=module.__name__, package=module.__package__)
            log = await interaction.original_response()
            await log.edit(content=log.content + "\nDone")

    @extension_reload.autocomplete(name="target")
    async def extension_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=i, value=i) for i in self.bot.extension_names if current.lower() in i.lower()]

    @app_commands.command(name="quickreload", description="Extensioを全て再読み込みします\nファイルの追加には対応しません")
    @is_owner()
    async def quick_reload(self, interaction: Interaction):
        await interaction.response.send_message(f"Reloading {len(self.bot.extensions)} modules ...", ephemeral=True)
        log = await interaction.original_response()
        for name in self.bot.extension_names:
            await log.edit(content=f"{log.content}\n> {name}")
            await self.bot.reload_extension(name=name)
        await log.edit(content=log.content + "\nDone")

    @app_commands.command(name="reload", description="Extensionを全てアンロードしてからロードします")
    @is_owner()
    async def reload(self, interaction: Interaction):
        await interaction.response.send_message(
            f"Unloading {len(self.bot.extension_names)} modules ...", ephemeral=True
        )
        log = await interaction.original_response()
        for name in self.bot.extension_names:
            await log.edit(content=log.content + f"\n> {name}")
            await self.bot.unload_extension(name=name)
        await log.edit(content=log.content + "\nDone")
        self.bot.load_extensions_folder()
        await log.edit(content=f"Loading {len(self.bot.extension_names)} modules ...")
        for name in self.bot.extension_names:
            await log.edit(content=log.content + f"\n> {name}")
            await self.bot.load_extension(name=name)
        await log.edit(content=log.content + "\nDone")

    @app_commands.command(name="restart", description="Botを再起動します")
    @is_owner()
    async def restart(self, interaction: Interaction):
        await interaction.response.send_message("Restarting ...", ephemeral=True)
        log = await interaction.original_response()
        self.bot.s.restart = True
        await log.edit(content=log.content + "\nDisconnect")
        await self.bot.close()

    @app_commands.command(name="close", description="Botを終了します")
    @is_owner()
    async def close(self, interaction: Interaction):
        await interaction.response.send_message("Disconnect", ephemeral=True)
        self.bot.s.restart = False
        await self.bot.close()

    @PasCog.listener("on_ready")
    async def on_ready(self):
        if "RESTART" in sys.argv:
            for id in self.bot.owner_ids:
                owner = await self.bot.fetch_user(id)
                await owner.send("Restarted")


async def setup(bot: PasBot):
    return await bot.add_cog(Power(bot))
