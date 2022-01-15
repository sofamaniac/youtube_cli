from screen import Screen, Directions

from application import Application
from keylistener import Listener
from keyconfig import configuration as config

import curses


def main(stdscr):
    app = Application(stdscr)
    listener = Listener(app)
    listener.start()
    last_event = None
    while True:
        c = app.scr.stdscr.getch()
        if c == config.quit:
            break
        elif c == config.down:
            app.select(Directions.Down)
        elif c == config.up:
            app.select(Directions.Up)
        elif c == config.left:
            app.select(Directions.Left)
        elif c == config.right:
            app.select(Directions.Right)
        elif c == config.pause:
            app.pause()
        elif c == config.next:
            app.next()
        elif c == config.prev:
            app.prev()
        elif c == config.prevPage:
            app.prev_page()
        elif c == config.nextPage:
            app.next_page()
        elif c == config.validate:
            app.enter()
        elif c == config.autoplay:
            app.setPlaylist()
        elif c == config.repeat:
            app.repeat()
        elif c == config.backward:
            app.forward(-5)
        elif c == config.forward:
            app.forward(5)
        elif c in config.percentJump:
            app.percentJump(config.percentJump.index(c)*10)
        elif c == config.mute:
            app.mute()
        elif c == config.incVolume:
            app.increaseVolume(5)
        elif c == config.decVolume:
            app.increaseVolume(-5)
        elif c == config.search:
            app.inSearch = True
        elif c == config.video:
            app.toggleVideo()
        elif c == config.shuffle:
            app.shuffle()
        elif c == config.reload:
            app.reload()
        elif c == config.addPlaylist:
            app.addToPlaylist()
        elif c == curses.ascii.ESC:
            app.escape()
        elif c == curses.KEY_RESIZE and last_event != curses.KEY_RESIZE:
            app.scr.resize()
        last_event = c

        app.update()

    listener.stop()
    app.quit()


if __name__ == "__main__":
    curses.wrapper(main)
