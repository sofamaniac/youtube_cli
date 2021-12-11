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
PLAYER_WIDTH = -1
PLAYER_HEIGHT = 5
CONTENT_HEIGHT = -1
OPTION_HEIGHT = 5

class Screen:

    def __init__(self, stdscr):

        curses.halfdelay(2)
        curses.curs_set(0)
        curses.use_default_colors()

        self.stdscr = stdscr

        self.initSizes()
        self.y, self.x = self.stdscr.getmaxyx()

        self.playerWin = curses.newwin(PLAYER_HEIGHT, PLAYER_WIDTH, CONTENT_HEIGHT, 1)
        self.playlistsWin = curses.newwin(PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 1)
        self.contentWin = curses.newwin(CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH + 1)
        self.informationWin = curses.newwin(CONTENT_HEIGHT - PLAYER_HEIGHT, PLAYLIST_WIDTH, PLAYER_HEIGHT, 1)
        self.optionWin = curses.newwin(OPTION_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT + 1, 1)

        # Redefining some colours to be less eye tiring
        curses.init_color(GREY, 825, 800, 800)
        curses.init_pair(1, GREY, -1) # -1 for terminal normal background

        curses.init_color(DARK_GREY, 300, 300,  0)
        curses.init_pair(2, DARK_GREY, -1)


    def update(self):
        self.checkResize
        curses.doupdate()

    def initSizes(self):
        global PLAYER_WIDTH, PLAYER_HEIGHT, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, CONTENT_WIDTH, CONTENT_HEIGHT

        PLAYER_WIDTH = curses.COLS - 2
        PLAYER_HEIGHT = 5
        PLAYLIST_WIDTH = curses.COLS // 5
        PLAYLIST_HEIGHT = 15
        CONTENT_WIDTH = curses.COLS -1 - PLAYLIST_WIDTH -1
        CONTENT_HEIGHT = curses.LINES - PLAYER_HEIGHT
        OPTION_HEIGHT = 5

    def resizeWindows(self):
        def aux(window, size_y, size_x, start_y, start_x):
            window.resize(size_y, size_x)
            window.move(start_y, start_x)
        aux(self.playerWin,PLAYER_HEIGHT, PLAYER_WIDTH, CONTENT_HEIGHT, 1)
        aux(self.playlistsWin, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, 0, 1)
        aux(self.contentWin, CONTENT_HEIGHT, CONTENT_WIDTH, 0, PLAYLIST_WIDTH + 1)
        aux(self.informationWin, CONTENT_HEIGHT - PLAYER_HEIGHT, PLAYLIST_WIDTH, PLAYER_HEIGHT, 1)
        aux(self.optionWin, OPTION_HEIGHT, PLAYLIST_WIDTH, PLAYLIST_HEIGHT + 1, 1)

    def checkResize(self):
        wasResized = self.stdscr.is_term_resized(self.y, self.x)
        if wasResized:
            self.initSizes()
            self.resizeWindows()
            self.y, self.x = self.stdscr.getmaxyx()



