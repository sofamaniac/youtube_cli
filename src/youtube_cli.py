"""Entry point for youtube_cli"""

import asyncio
import curses

from application import Application
from keyconfig import KeyConfiguration

# setting up logger
import logging

from config import *

import mpris

from gui.screen import stdscr, curses_settings, reset_curses

logging.basicConfig(
    level=logging.INFO,
    filename=dirs.user_log_dir + "/youtube_cli.log",
    filemode="w",
    format="%(asctime)s:%(filename)10s:%(message)s",
)


async def initialize(stdscr):
    """Initialize the different component of the application"""
    curses_settings(stdscr)
    app = Application(stdscr)
    await app.init()
    config = KeyConfiguration(app)
    mpris.initialize(app)
    return await main(app, config)


async def main(app, config):
    """Entry point of the program"""
    last_event = None
    while True:
        char = app.scr.get_wch()
        if char == curses.KEY_RESIZE and last_event != curses.KEY_RESIZE:
            app.resize()
        else:
            await config.check_action(char)
        last_event = char
        await app.update()
    end(app)


def end(app):
    """Gracefully quit everything"""
    reset_curses(stdscr)
    app.quit()


if __name__ == "__main__":
    asyncio.run(initialize(stdscr))
