"""Entry point for youtube_cli"""

import curses

from application import Application
from keyconfig import KeyConfiguration

# setting up logger
import logging

from config import *

import mpris

logging.basicConfig(
    level=logging.DEBUG,
    filename=dirs.user_log_dir + "/youtube_cli.log",
    filemode="w",
    format="%(asctime)s:%(filename)10s:%(message)s",
)


def initialize(stdscr):
    """Initialize the different component of the application"""
    app = Application(stdscr)
    config = KeyConfiguration(app)
    mpris.initialize(app)
    return main(app, config)


def main(app, config):
    """Entry point of the program"""
    last_event = None
    while True:
        char = app.scr.get_wch()
        if char == curses.KEY_RESIZE and last_event != curses.KEY_RESIZE:
            app.resize()
        else:
            config.check_action(char)
        last_event = char
        app.update()
    end(app)


def end(app):
    """Gracefully quit everything"""
    app.quit()


if __name__ == "__main__":
    curses.wrapper(initialize)
