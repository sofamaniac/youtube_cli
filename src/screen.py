import curses
from enum import Enum

class Directions(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3

# Color pairs index
COLOR_TEXT = 1
COLOR_BORDER = 2

# Colors
GREY = 8
DARK_GREY = 9

# Windows dimensions
PLAYLIST_WIDTH = 30
PLAYLIST_HEIGHT = 15
CONTENT_WIDTH = -1
PLAYER_HEIGHT = 5
CONTENT_HEIGHT = -1

class Screen:

    def __init__(self, stdscr):
        global PLAYER_HEIGHT, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, CONTENT_WIDTH, CONTENT_HEIGHT

        curses.halfdelay(2)
        curses.curs_set(0)
        curses.use_default_colors()

        self.stdscr = stdscr

        PLAYER_HEIGHT = 5
        PLAYLIST_WIDTH = curses.COLS // 5
        PLAYLIST_HEIGHT = 15
        CONTENT_WIDTH = curses.COLS -1 - PLAYLIST_WIDTH -1
        CONTENT_HEIGHT = curses.LINES - PLAYER_HEIGHT

        self.playerWin = curses.newwin(PLAYER_HEIGHT, curses.COLS-1, CONTENT_HEIGHT, 0)
        self.playlistsWin = curses.newwin(PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 0)
        self.contentWin = curses.newwin(CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH + 1)
        self.informationWin = curses.newwin(CONTENT_HEIGHT - PLAYER_HEIGHT, PLAYLIST_WIDTH, PLAYER_HEIGHT, 0)

        # Redefining some colours to be less eye tiring
        curses.init_color(GREY, 825, 800, 800)
        curses.init_pair(1, GREY, -1) # -1 for terminal normal background

        curses.init_color(DARK_GREY, 300, 300,  0)
        curses.init_pair(2, DARK_GREY, -1)


    def update(self):
        curses.doupdate()

