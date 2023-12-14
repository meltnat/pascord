import json
import os

from setting import Setting


class DiscordSetting(Setting):
    token: str
    command_prefix: str
    guild: SyntaxWarning

    def default(self) -> None:
        super().default()
        self.command_prefix = "/"
        self.guild = 1064209224206401556


class FolderSettting(Setting):
    settings: str
    logs: str
    extensions: str
    resource: str

    def default(self) -> None:
        super().default()
        self.settings = "/settings/"
        self.logs = "/logs/"
        self.extensions = "/src/extensions/"
        self.resource = "/resource/"


class PathSetting(Setting):
    folder: FolderSettting

    def __init__(self) -> None:
        self.folder = FolderSettting()


class PasSetting(Setting):
    discord: DiscordSetting
    path: PathSetting

    def __init__(self) -> None:
        self.discord = DiscordSetting()
        self.path = PathSetting()

        self.discord.token = os.getenv("TOKEN")
        self.debug = os.getenv("DEBUG", "FALSE").upper() == "TRUE"

    def default(self) -> None:
        super().default()
        self.changeonsave = False

    def load_file(self) -> None:
        try:
            with open(file=self.path.folder.settings + "Setting.json", mode="r", encoding="utf-8") as f:
                self = json.load(f)
        except FileNotFoundError as e:
            pass

    def save_file(self) -> None:
        with open(file=self.path.folder.settings + "Setting.json", mode="wa", encoding="utf-8") as f:
            json.dump(obj=self, fp=f, indent=4, ensure_ascii=False)
