import curses
from enum import Enum
import sys
import locale
import wcwidth
import _curses


class Directions(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class CurseString:
    def __init__(self, string):
        self.string = string
        self.effects = [curses.color_pair(COLOR_TEXT) for s in string]

    def find_max(self, max_len):
        i = 0  # current character
        p = 0  # position on screen
        while i < len(self.string) and p <= max_len:
            p += wcwidth.wcwidth(self.string[i])  # some characters take 2 cells
            i += 1
        if p > max_len:
            while p > max_len - 3:
                i -= 1
                p -= wcwidth.wcwidth(self.string[i])
        return i, i < len(self.string)

    def draw_to_win(self, dest, start_y, start_x, max_len):
        max_pos, is_long = self.find_max(max_len)
        p = 0
        for i in range(max_pos):
            dest.addstr(start_y, start_x + p, self.string[i], self.effects[i])
            p += wcwidth.wcwidth(self.string[i])
        if is_long:
            dest.addstr(
                start_y, start_x + max_len - 3, "...", self.effects[max_pos - 1]
            )

    def color(self, color, start=-1e99, end=1e99):
        start = max(start, 0)
        end = min(end, len(self.string))
        for i in range(start, end):
            self.effects[i] |= curses.color_pair(color)

    def set_attr(self, attr, start=-1e99, end=1e99):
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
        curses.set_escdelay(20)
        curses.curs_set(0)
        curses.use_default_colors()

        self.stdscr = stdscr

        self.initSizes()

        self.wins = []

        # Redefining some colours to be less eye tiring
        curses.init_color(GREY, 825, 800, 800)
        curses.init_pair(COLOR_TEXT, GREY, -1)  # -1 for terminal normal background

        curses.init_color(DARK_GREY, 300, 300, 0)
        curses.init_pair(COLOR_BORDER, DARK_GREY, -1)

        curses.init_color(10, 800, 300, 300)
        curses.init_pair(COLOR_SEG, 10, -1)

    def get_wch(self):
        try:
            return self.stdscr.get_wch()
        except _curses.error:
            return -1

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
        global PLAYER_WIDTH, PLAYER_HEIGHT, PLAYLIST_HEIGHT, PLAYLIST_WIDTH, CONTENT_WIDTH, CONTENT_HEIGHT, OPTION_HEIGHT, INFO_HEIGHT, SEARCH_WIDTH, SEARCH_HEIGHT

        PLAYER_WIDTH = self.max_x
        PLAYER_HEIGHT = 4

        PLAYLIST_WIDTH = max(1, self.max_x // 5)
        PLAYLIST_HEIGHT = min(15, self.max_y // 4)

        CONTENT_WIDTH = self.max_x - PLAYLIST_WIDTH
        CONTENT_HEIGHT = self.max_y - PLAYER_HEIGHT

        OPTION_HEIGHT = 2 + NB_OPTIONS

        INFO_HEIGHT = 5

        SEARCH_WIDTH = 3 * self.max_x // 5
        SEARCH_HEIGHT = 3

    def resizeWindows(self, old_w, old_h):
        """Tries to resize all windows while preserving their previous proportions, [old_w] and [old_h]
        are the previous dimensions of the whole screen"""
        # TODO: may be necessary to order the windows first to avoid errors (ordre usuel sur NxN)
        for w in self.wins:
            # TODO : tenter de préserver les proportions tout en réduisant la taille
            pass

    def resize(self):
        old_w = self.max_x
        old_h = self.max_y
        curses.resizeterm(*self.stdscr.getmaxyx())
        self.initSizes()
        self.resizeWindows(old_w, old_h)
        self.stdscr.erase()

    def add_win(self, y, x, h, w):
        """Add window to current string"""

        self.wins.append(curses.newwin(h, w, y, x))
        return self.wins[-1]
