import logging
import os
import sys
from logging import Logger, handlers

from pasbot import PasBot
from pasSetting import PasSetting


def logger(s: PasSetting, module: str) -> Logger:
    folder = os.getcwd() + s.path.folder.logs
    if not os.path.exists(folder):
        os.mkdir(folder)

    logger = logging.getLogger(module)
    logger.handlers.clear()

    streamHandler = logging.StreamHandler()
    fileHandler = handlers.RotatingFileHandler(folder + module + ".log", maxBytes=10000, backupCount=5)
    streamHandler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] (%(filename)s | %(funcName)s | %(lineno)s) %(message)s")
    )
    fileHandler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] (%(filename)s | %(funcName)s | %(lineno)s) %(message)s")
    )

    logger.setLevel(logging.DEBUG)
    streamHandler.setLevel(logging.INFO)
    fileHandler.setLevel(logging.DEBUG)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)

    return logger


if __name__ == "__main__":
    print("Initializing...")
    s = PasSetting()
    s.default()
    s.load_file()

    logger(s, "discord")

    bot = PasBot(setting=s)

    print("Connecting ...")
    bot.run(token=s.discord.token)
    if s.restart:
        sys.exit(233)
    sys.exit(0)
