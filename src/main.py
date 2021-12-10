import mpv

import youtube
from screen import Screen, Directions

from application import Application
from keylistener import Listener

import curses
from time import sleep

yt = youtube.YoutbeHandler()

def main(stdscr):
    app = Application(stdscr)
    listener = Listener(app)
    listener.start()
    while True:
        c = app.scr.stdscr.getch()
        if c == ord('q'):
            break
        elif c == ord('j'):
            app.select(Directions.Down)
        elif c == ord('k'):
            app.select(Directions.Up)
        elif c == ord('h'):
            app.select(Directions.Left)
        elif c == ord('l'):
            app.select(Directions.Right)
        elif c == ord(' '):
            app.pause()
        elif c == ord('>'):
            app.next()
        elif c == ord('<'):
            app.prev()
        elif c == ord('p'):
            app.prev_page()
        elif c == ord('n'):
            app.next_page()
        elif c == ord('\n'):
            app.enter()
        elif c == ord('a'):
            app.setPlaylist()
        elif c == ord('r'):
            app.repeat()
        elif c == curses.KEY_LEFT:
            app.forward(-5)
        elif c == curses.KEY_RIGHT:
            app.forward(5)
        elif c == ord('m'):
            app.mute()
        elif c == ord('d'):
            app.increaseVolume(-5)
        elif c == ord('f'):
            app.increaseVolume(5)


        app.update()
    listener.stop()


if __name__ == "__main__":
    curses.wrapper(main)
