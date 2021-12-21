import mpv

from screen import Screen, Directions

from application import Application
from keylistener import Listener

import curses

def main(stdscr):
    app = Application(stdscr)
    listener = Listener(app)
    listener.start()
    last_event = None
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
        elif c == curses.KEY_RESIZE and last_event != curses.KEY_RESIZE:
            # for some reason we need to resize two times in order for the effects be felt
            app.scr.resize()
            app.scr.resize()
        elif c == ord('s'):
            app.inSearch = True
        last_event = c


        app.update()
    listener.stop()
    app.quit()


if __name__ == "__main__":
    curses.wrapper(main)
