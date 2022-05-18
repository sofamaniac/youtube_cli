"""Entry point for youtube_cli"""

import curses

from application import Application
from keylistener import Listener
from keyconfig import KeyConfiguration

# setting up logger
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="youtube_cli.log",
    filemode="w",
    format="%(asctime)s:%(filename)10s:%(message)s",
)


def initialize(stdscr):
    """Initialize the different component of the application"""
    app = Application(stdscr)
    config = KeyConfiguration(app)
    listener = Listener(app)
    listener.start()
    return main(app, listener, config)


def main(app, listener, config):
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
    end(listener, app)


def end(listener, app):
    """Gracefully quit everything"""
    listener.stop()
    app.quit()


if __name__ == "__main__":
    curses.wrapper(initialize)
