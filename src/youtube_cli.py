from screen import Screen, Directions

from application import Application
from keylistener import Listener

import curses

from keyconfig import KeyConfiguration

def initialize(stdscr):
    app = Application(stdscr)
    config = KeyConfiguration(app)
    listener = Listener(app)
    listener.start()
    return main(app, listener, config)

def main(app, listener, config):
    last_event = None
    while True:
        c = app.scr.stdscr.getch()
        if c == curses.KEY_RESIZE and last_event != curses.KEY_RESIZE:
            app.scr.resize()
        else:
            config.checkAction(c)
        last_event = c
        app.update()
    quit(listener, app)

def quit(listener, app):
    listener.stop()
    app.quit()


if __name__ == "__main__":
    curses.wrapper(initialize)
