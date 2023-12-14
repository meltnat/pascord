from __future__ import annotations

from enum import Enum
import os
import random

from discord import (
    ButtonStyle,
    Embed,
    Interaction,
    InteractionMessage,
    Member,
    TextStyle,
    app_commands,
    ui,
)
from discord.abc import User
from discord.components import SelectOption
from discord.interactions import Interaction

import gspread
from gspread.client import Client
from oauth2client.service_account import ServiceAccountCredentials

from pasbot import PasBot
from pascog import PasCog
from setting import Setting

INDEX_ID = "1MfRVWgsokRmt10HChbJ3ERpcS1yOPk2xzUTD8RxRlbA"


class IndexPermission(Enum):
    PUBLIC = 0
    PRIVATE = 1


class Category:
    name: str
    description: str
    id: str
    permission: IndexPermission
    guilds: list[str]

    def __init__(
        self,
        *,
        name: str = "",
        description: str = "",
        id: str = "",
        permission: IndexPermission = IndexPermission.PUBLIC,
        guilds: list[int] = [],
    ) -> None:
        self.name = name
        self.description = description
        self.id = id
        self.permission = permission
        self.guilds = guilds


class Session:
    ito: Ito
    owner: User
    initView: ui.View
    message: InteractionMessage
    id: int
    players: list[User]
    client: Client
    index: list[Category]
    category: Category
    setting: Setting

    def load_index(self, guild_id: int):
        self.index = []
        data = self.client.open_by_key(INDEX_ID).sheet1.get_all_values()
        labels = data.pop(0)
        for line in data:
            category = Category()
            for i, label in enumerate(labels):
                match label.lower():
                    case "name":
                        category.name = line[i]
                    case "description":
                        category.description = line[i]
                    case "id":
                        category.id = line[i]
                    case "permission":
                        category.permission = IndexPermission[line[i].upper()]
                    case "guilds":
                        category.guilds = line[i].split(",")
            if category.permission == IndexPermission.PUBLIC:
                self.index.append(category)
            if category.permission == IndexPermission.PRIVATE and str(guild_id) in category.guilds:
                self.index.append(category)

    def __init__(self, ito: Ito, owner: User, id: int, setting: Setting, guild_id: int):
        self.ito = ito
        self.owner = owner
        self.id = id
        self.players = [owner]
        self.setting = setting
        self.client = gspread.authorize(
            credentials=ServiceAccountCredentials.from_json_keyfile_name(
                os.getcwd() + self.setting.path.folder.resource + "ito/credential.json",
                [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
        )
        self.load_index(guild_id=guild_id)
        self.category = random.choice(self.index)

    def init(self):
        self.initView = InitView(self)
        return self.initView

    async def start(self) -> None:
        await self.message.edit(content="Generating", embed=None, view=None)
        sheet = self.client.open_by_url(self.category.id).sheet1
        data = sheet.get_all_values()
        data.pop(0)
        theme = random.choice([(line[1], line[2]) for line in data])
        view = IngameView(self, theme=theme[0], description=theme[1])
        await self.message.edit(content=None, embed=view.content(), view=view)

    def exist_player(self, player: User) -> bool:
        for u in self.players:
            if u.id == player.id:
                return True
        return False

    def remove_player(self, player: User) -> None:
        for u in self.players:
            if u.id == player.id:
                self.players.remove(u)


class Player:
    user: User
    number: int
    example: str
    opened: bool

    def __init__(self, user: User, number: int) -> None:
        self.user = user
        self.number = number
        self.example = ""
        self.opened = False

    def __eq__(self, __value: object) -> bool:
        if type(__value) is Player:
            return __value.user.id == self.user.id and __value.number == self.number and __value.example == self.example
        return False


class NewGameView(ui.View):
    session: Session

    def __init__(self, session: Session):
        super().__init__(timeout=120)
        self.session = session

    @ui.button(label="新規ゲーム", style=ButtonStyle.success)
    async def new(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(content="Generating")
        await self.session.message.edit(view=None)
        session = Session(
            self.session.ito, interaction.user, interaction.id, self.session.setting, guild_id=interaction.guild_id
        )
        session.ito.sessions.append(session)
        view = session.init()
        session.message = await interaction.original_response()
        session.players = self.session.players.copy()
        await session.message.edit(content="", embed=view.content(), view=view)

    async def on_timeout(self):
        await super().on_timeout()
        await self.session.message.edit(view=None)


class IngameView(ui.View):
    session: Session
    players: list[Player]
    theme: str
    description: str

    def __init__(self, session: Session, theme: str, description: str):
        super().__init__(timeout=None)
        self.session = session
        self.theme = theme
        self.description = description
        self.players = []
        ilist = list(range(1, 101))
        for user in self.session.players:
            i = ilist[random.randint(0, len(ilist) - 1)]
            ilist.remove(i)
            self.players.append(Player(user, i))
        self.add_item(OrderSelect(self))

    def content(self, color=0x0000FF) -> Embed:
        embed = Embed()
        embed.title = f"SessionID:{self.session.id}"
        embed.description = f"{len(self.players)} players"
        embed.color = color
        embed.add_field(name="お題:" + self.theme, value=self.description, inline=False)
        d = {1: "st", 2: "nd", 3: "rd"}
        for i, player in enumerate(self.players):
            q, mod = divmod(i + 1, 10)
            name = f"{i+1}{q % 10 != 1 and d.get(mod) or 'th'}"
            if player.opened:
                name += f", {player.number}"
            embed.add_field(name=name, value=f"{player.user.mention}: {player.example}")
        return embed

    def get_player(self, target: int | User) -> Player | None:
        id = None
        if type(target) is int:
            id = target
        else:
            id = target.id
        for player in self.players:
            if player.user.id == id:
                return player
        return None

    def get_order(self, target: Player | int | User | Member) -> int | None:
        id = None
        if type(target) is int:
            id = target
        elif type(target) is Player:
            id = target.user.id
        else:
            id = target.id
        for i, p in enumerate(self.players):
            if id == p.user.id:
                return i
        return None

    async def update_content(self, color=0x0000FF) -> None:
        await self.session.message.edit(embed=self.content(color=color))

    @ui.button(label="入力", style=ButtonStyle.success)
    async def input(self, interaction: Interaction, button: ui.Button):
        player = self.get_player(interaction.user)
        if player is None:
            await interaction.response.defer()
        else:
            await interaction.response.send_modal(ExampleInputModal(view=self, player=player))

    @ui.button(label="公開", style=ButtonStyle.red)
    async def open(self, interaction: Interaction, button: ui.Button):
        player = self.get_player(interaction.user)
        if player is not None and not player.opened:
            await interaction.response.send_modal(OpenModal(player=player, view=self))


class OpenModal(ui.Modal):
    player: Player
    ingameView: IngameView

    def __init__(self, player: Player, view: IngameView) -> None:
        super().__init__(title="公開しますか?", timeout=30)
        self.player = player
        self.ingameView = view
        self.add_item(ui.TextInput(label="何か入力してください"))

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.player.opened = True
        if not [i for i in self.ingameView.players if not i.opened]:
            await self.ingameView.update_content(color=0xFF00FF)
            self.ingameView.session.ito.sessions.remove(self.ingameView.session)
            await self.ingameView.session.message.edit(view=NewGameView(self.ingameView.session))
        else:
            await self.ingameView.update_content()

    async def on_timeout(self) -> None:
        await super().on_timeout()


class OrderSelect(ui.Select):
    ingameView: IngameView

    def __init__(self, view: IngameView) -> None:
        super().__init__(placeholder="")
        self.ingameView = view
        self.update_options()

    def update_options(self) -> None:
        self.options = [
            SelectOption(label=str(i + 1), value=str(i), description=p.user.name)
            for i, p in enumerate(self.ingameView.players)
        ]

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        i1 = int(self.values[0])
        i2 = self.ingameView.get_order(interaction.user)
        self.ingameView.players[i1], self.ingameView.players[i2] = (
            self.ingameView.players[i2],
            self.ingameView.players[i1],
        )
        self.update_options()
        await self.ingameView.update_content()


class ExampleInputModal(ui.Modal):
    ingameView: IngameView
    player: Player
    input: ui.TextInput

    def __init__(self, view: IngameView, player: Player) -> None:
        super().__init__(title=f"{view.theme} / {player.number}", timeout=None)
        self.ingameView = view
        self.player = player
        self.input = ui.TextInput(
            label=f"例を入力してください",
            style=TextStyle.short,
            placeholder="Banana",
            default=self.player.example,
            required=True,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()
        self.player.example = str(self.input)
        await self.ingameView.update_content()


class InitView(ui.View):
    session: Session

    def __init__(self, session: Session):
        super().__init__(timeout=None)
        self.session = session
        self.add_item(ThemeSelect(self))

    def content(self) -> Embed:
        embed = Embed()
        embed.title = f"SessionID:{self.session.id}"
        embed.description = f"@here {self.session.owner.mention}が新規Itoセッションを始めました"
        embed.color = 0x00FF00
        embed.add_field(
            name="お題:" + self.session.category.name,
            value=self.session.category.description,
        )
        embed.add_field(
            name=f"Players:{len(self.session.players)}",
            value="".join([u.mention for u in self.session.players]),
        )
        return embed

    async def update_content(self) -> None:
        await self.session.message.edit(embed=self.content())

    @ui.button(label="開始", style=ButtonStyle.blurple)
    async def start(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id == self.session.owner.id:
            await interaction.response.defer()
            await self.session.start()
        else:
            await interaction.response.defer()

    @ui.button(label="参加", style=ButtonStyle.green)
    async def join(self, interaction: Interaction, button: ui.Button):
        if self.session.exist_player(interaction.user):
            await interaction.response.send_message(
                f"すでに参加しています",
                ephemeral=True,
            )
            return
        self.session.players.append(interaction.user)
        await self.update_content()
        await interaction.response.send_message(f"{interaction.user.mention}プレイヤーリストに追加しました", ephemeral=True)

    @ui.button(label="非参加", style=ButtonStyle.gray)
    async def unjoin(self, interaction: Interaction, button: ui.Button):
        if self.session.exist_player(interaction.user):
            self.session.remove_player(interaction.user)
            await self.update_content()
            await interaction.response.send_message(f"{interaction.user.mention}プレイヤーリストから削除しました", ephemeral=True)
        else:
            await interaction.response.defer()


class ThemeSelect(ui.Select):
    initView: InitView

    def __init__(self, view: InitView):
        self.initView = view
        options = [
            SelectOption(label=i.name, value=i.name, description=i.description) for i in self.initView.session.index
        ]
        super().__init__(placeholder="", options=options)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.initView.session.category = [i for i in self.initView.session.index if i.name == self.values[0]][0]
        await self.initView.update_content()


class Ito(PasCog):
    sessions: list[Session]
    client: Client

    def __init__(self, bot: PasBot) -> None:
        super().__init__(bot)
        self.sessions = []

    @app_commands.command(name="ito", description="新規Itoセッションを開始します")
    async def init(self, interaction: Interaction):
        session = Session(self, interaction.user, interaction.id, self.bot.s, guild_id=interaction.guild_id)
        self.sessions.append(session)
        view = session.init()
        await interaction.response.send_message(content="Generating")
        session.message = await interaction.original_response()
        await session.message.edit(content="", embed=view.content(), view=view)


async def setup(bot: PasBot):
    return await bot.add_cog(Ito(bot))
