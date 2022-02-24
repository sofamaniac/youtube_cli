import curses
from enum import Enum
import sys
import locale
import wcwidth


class Directions(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3

class CurseString:
    def __init__(self, string):
        self.string = string
        self.effects = [curses.color_pair(COLOR_TEXT) for s in string]

    def findMax(self, maxLen):
        i = 0  # current character
        p = 0  # position on screen
        while i < len(self.string) and p <= maxLen:
            p += wcwidth.wcwidth(self.string[i])  # some characters take 2 cells
            i += 1
        if p > maxLen:
            while p > maxLen - 3:
                i -= 1
                p -= wcwidth.wcwidth(self.string[i])
        return i, i < len(self.string)

    def drawToWin(self, dest, startY, startX, maxLen):
        max_pos, isLong = self.findMax(maxLen)
        p = 0
        for i in range(max_pos):
            dest.addstr(startY, startX+p, self.string[i], self.effects[i])
            p += wcwidth.wcwidth(self.string[i])
        if isLong:
            dest.addstr(startY, startX+maxLen-3, '...', self.effects[max_pos-1])


    def color(self, color, start=-1e99, end=1e99):
        start = max(start, 0)
        end = min(end, len(self.string))
        for i in range(start, end):
            self.effects[i] |= curses.color_pair(color)

    def setAttr(self, attr, start=-1e99, end=1e99):
        start = max(start, 0)
        end = min(end, len(self.string))
        for i in range(start, end):
            self.effects[i] |= attr

# Color pairs index
COLOR_TEXT = 1
COLOR_BORDER = 2
COLOR_SEG = 3

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

        locale.setlocale(locale.LC_ALL, "")
        locale.setlocale(locale.LC_NUMERIC, "C")

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

        self.commandField = curses.newwin(1, PLAYER_WIDTH, self.max_y -1, 0)

        # Redefining some colours to be less eye tiring
        curses.init_color(GREY, 825, 800, 800)
        curses.init_pair(COLOR_TEXT, GREY, -1)  # -1 for terminal normal background

        curses.init_color(DARK_GREY, 300, 300, 0)
        curses.init_pair(COLOR_BORDER, DARK_GREY, -1)
        
        curses.init_color(10, 800, 300, 300)
        curses.init_pair(COLOR_SEG, 10, -1)

    @property
    def max_x(self):
        return curses.COLS
    
    @property
    def max_y(self):
        return curses.LINES

    def center(self, window):
        height, width = window.getmaxyx()

        new_x = (self.max_x - width) // 2
        new_y = (self.max_y - height) // 2

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
