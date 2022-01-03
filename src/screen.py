import curses
from enum import Enum
import sys


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
CONTENT_HEIGHT = -1

PLAYER_WIDTH = -1
PLAYER_HEIGHT = 5

NB_OPTIONS = 5
OPTION_HEIGHT = 2 + NB_OPTIONS
INFO_HEIGHT = 5

SEARCH_WIDTH = 80
SEARCH_HEIGHT = 3

class Screen:
    def __init__(self, stdscr):

        curses.halfdelay(2)
        curses.curs_set(0)
        curses.use_default_colors()

        self.stdscr = stdscr

        self.initSizes()

        self.playerWin = curses.newwin(PLAYER_HEIGHT, PLAYER_WIDTH, CONTENT_HEIGHT, 0)
        self.playlistsWin = curses.newwin(PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 0)
        self.contentWin = curses.newwin(CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH)
        self.optionWin = curses.newwin(OPTION_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT, 0)
        self.informationWin = curses.newwin(INFO_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT + OPTION_HEIGHT, 0)
        self.searchWin = curses.newwin(SEARCH_HEIGHT, SEARCH_WIDTH, 0, 0)
        self.center(self.searchWin)
        y, x = self.searchWin.getbegyx()
        self.searchField = self.searchWin.subwin(SEARCH_HEIGHT - 2, SEARCH_WIDTH - 2, y+1,  x+1)
        self.addPlaylistWin = curses.newwin(PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 0)
        self.center(self.addPlaylistWin)

        # Redefining some colours to be less eye tiring
        curses.init_color(GREY, 825, 800, 800)
        curses.init_pair(1, GREY, -1)  # -1 for terminal normal background

        curses.init_color(DARK_GREY, 300, 300, 0)
        curses.init_pair(2, DARK_GREY, -1)

    def center(self, window):
        max_x = curses.COLS
        max_y = curses.LINES

        height, width = window.getmaxyx()

        new_x = (max_x - width) // 2
        new_y = (max_y - height) // 2

        window.resize(1, 1)
        window.mvwin(new_y, new_x)
        window.resize(height, width)

    def update(self):
        curses.doupdate()

    def initSizes(self):
        global PLAYER_WIDTH, PLAYER_HEIGHT, \
                PLAYLIST_HEIGHT, PLAYLIST_WIDTH, \
                CONTENT_WIDTH, CONTENT_HEIGHT, \
                OPTION_HEIGHT, INFO_HEIGHT, \
                SEARCH_WIDTH, SEARCH_HEIGHT

        max_x = curses.COLS
        max_y = curses.LINES

        PLAYER_WIDTH = max_x
        PLAYER_HEIGHT = 4

        PLAYLIST_WIDTH = max(1, max_x // 5)
        PLAYLIST_HEIGHT = min(15, max_y // 4)

        CONTENT_WIDTH = max_x - PLAYLIST_WIDTH
        CONTENT_HEIGHT = max_y - PLAYER_HEIGHT

        OPTION_HEIGHT = 2 + NB_OPTIONS

        INFO_HEIGHT = 5

        SEARCH_WIDTH = 3 * max_x // 5
        SEARCH_HEIGHT = 3  # rework formula to ensure that one can input 80 chars in the search box TODO

    def resizeWindows(self):
        def aux(window, size_y, size_x, start_y, start_x):
            window.resize(size_y, size_x)
            window.mvwin(start_y, start_x)

        aux(self.playlistsWin, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 0)
        aux(self.optionWin, OPTION_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT, 0)
        aux(self.informationWin, INFO_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT + OPTION_HEIGHT, 0)
        aux(self.contentWin, CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH)
        aux(self.playerWin, PLAYER_HEIGHT, PLAYER_WIDTH, CONTENT_HEIGHT, 0)

        aux(self.addPlaylistWin, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 0)
        self.center(self.addPlaylistWin)

        aux(self.searchWin, SEARCH_HEIGHT, SEARCH_WIDTH, 0, 0)
        self.center(self.searchWin)
        y, x = self.searchWin.getbegyx()
        aux(self.searchField, SEARCH_HEIGHT-2, SEARCH_WIDTH-2, y+1, x+1)

    def resize(self):
        curses.resizeterm(*self.stdscr.getmaxyx())
        self.initSizes()
        self.resizeWindows()
        self.stdscr.erase()
