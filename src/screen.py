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

NB_OPTIONS = 4
OPTION_HEIGHT = 2+NB_OPTIONS
INFO_HEIGHT = 5

SEARCH_WIDTH = 80
SEARCH_HEIGHT = 3
SEARCH_Y = 10
SEARCH_X = 10

class Screen:

    def __init__(self, stdscr):

        curses.halfdelay(2)
        curses.curs_set(0)
        curses.use_default_colors()

        self.stdscr = stdscr

        self.initSizes()

        self.playerWin      = curses.newwin(PLAYER_HEIGHT, PLAYER_WIDTH, CONTENT_HEIGHT, 1)
        self.playlistsWin   = curses.newwin(PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 1)
        self.contentWin     = curses.newwin(CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH + 1)
        self.optionWin      = curses.newwin(OPTION_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT + 1, 1)
        self.informationWin = curses.newwin(INFO_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT+1+OPTION_HEIGHT+1, 1)
        self.searchWin      = curses.newwin(SEARCH_HEIGHT, SEARCH_WIDTH, SEARCH_Y, SEARCH_X)
        self.searchField    = self.searchWin.subwin(SEARCH_HEIGHT-2, SEARCH_WIDTH-2, SEARCH_Y+1, SEARCH_X+1)

        # Redefining some colours to be less eye tiring
        curses.init_color(GREY, 825, 800, 800)
        curses.init_pair(1, GREY, -1) # -1 for terminal normal background

        curses.init_color(DARK_GREY, 300, 300,  0)
        curses.init_pair(2, DARK_GREY, -1)


    def update(self):
        curses.doupdate()

    def initSizes(self):
        global PLAYER_WIDTH, PLAYER_HEIGHT, \
        PLAYLIST_HEIGHT, PLAYLIST_WIDTH, \
        CONTENT_WIDTH, CONTENT_HEIGHT, \
        OPTION_HEIGHT, INFO_HEIGHT, \
        SEARCH_WIDTH, SEARCH_HEIGHT, SEARCH_X, SEARCH_Y

        PLAYER_WIDTH = curses.COLS - 2
        PLAYER_HEIGHT = 4

        PLAYLIST_WIDTH = max(1, curses.COLS // 5)
        PLAYLIST_HEIGHT = min(15, curses.LINES //4)

        CONTENT_WIDTH = curses.COLS -1 - PLAYLIST_WIDTH -1
        CONTENT_HEIGHT = curses.LINES - PLAYER_HEIGHT -1

        OPTION_HEIGHT = 2 + NB_OPTIONS

        INFO_HEIGHT = 5

        SEARCH_WIDTH = 3*curses.COLS // 5
        SEARCH_HEIGHT = 3  # rework formula to ensure that one can input 80 chars in the search box TODO
        SEARCH_Y = curses.LINES//2 - 1
        SEARCH_X = curses.COLS // 5

    def resizeWindows(self):
        def aux(window, size_y, size_x, start_y, start_x):
            window.resize(1, 1)  # avoid moving windows that are too big in the next instruction
            window.mvwin(start_y, start_x)
            window.resize(size_y, size_x)
        aux(self.playlistsWin, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 1)
        aux(self.optionWin, OPTION_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT + 1, 1)
        aux(self.informationWin, INFO_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT+1+OPTION_HEIGHT+1, 1)
        aux(self.contentWin, CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH+1)
        aux(self.playerWin, PLAYER_HEIGHT, PLAYER_WIDTH, CONTENT_HEIGHT, 1)
        aux(self.searchWin, SEARCH_HEIGHT, SEARCH_WIDTH, SEARCH_Y, SEARCH_X)

    def resize(self):
        self.initSizes()
        self.resizeWindows()
        curses.resizeterm(*self.stdscr.getmaxyx())
        self.stdscr.erase()

