from enum import Enum
import sys
import locale
import wcwidth

class Directions(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3

from notcurses import Notcurses


nc = Notcurses()

COLOR_BORDER = None
TEXT_COLOR = (200, 200, 200, 0)
BACKGROUND_COLOR = (0, 0, 0, 0) 

# Windows dimensions,
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

class CurseString:
    def __init__(self, string):
        self.string = string
        #self.effects = [curses.color_pair(COLOR_TEXT) for s in string]
        self.effects = [0 for s in string]

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
            dest.putstr_yx(startY, startX+p, self.string[i])
            p += wcwidth.wcwidth(self.string[i])
        if isLong:
            dest.putstr_yx(startY, startX+maxLen-3, '...')


    def color(self, color, start=-1e99, end=1e99):
        start = max(start, 0)
        end = min(end, len(self.string))
        for i in range(start, end):
            #self.effects[i] |= curses.color_pair(color)
            self.effects[i] = 0

    def setAttr(self, attr, start=-1e99, end=1e99):
        start = max(start, 0)
        end = min(end, len(self.string))
        for i in range(start, end):
            self.effects[i] |= attr

class Screen:
    
    def __init__(self):

        self.plane = nc.stdplane()

        locale.setlocale(locale.LC_ALL, "")
        #locale.setlocale(locale.LC_NUMERIC, "C")

        self.initSizes()

        self.playerWin = self.plane.create(rows=PLAYER_HEIGHT, cols=PLAYER_WIDTH, x_pos=0, y_pos=CONTENT_HEIGHT)
        self.playlistsWin = self.plane.create(rows=PLAYLIST_HEIGHT, cols=PLAYLIST_WIDTH, x_pos=0, y_pos=0)
        self.contentWin = self.plane.create(rows=CONTENT_HEIGHT, cols=CONTENT_WIDTH, y_pos=0, x_pos=PLAYLIST_WIDTH)
        self.optionWin = self.plane.create(rows=OPTION_HEIGHT, cols=PLAYLIST_WIDTH, y_pos=PLAYLIST_HEIGHT, x_pos=0)
        self.informationWin = self.plane.create(rows=INFO_HEIGHT, cols=PLAYLIST_WIDTH, y_pos=PLAYLIST_HEIGHT + OPTION_HEIGHT, x_pos=0)
        self.searchWin = self.plane.create(rows=SEARCH_HEIGHT, cols=SEARCH_WIDTH, y_pos=0, x_pos=0)
        self.center(self.searchWin)
        y, x = self.searchWin.yx()
        self.searchField = self.searchWin.create(rows=SEARCH_HEIGHT - 2, cols=SEARCH_WIDTH -2)
        self.addPlaylistWin = self.plane.create(rows=PLAYLIST_HEIGHT, cols=PLAYLIST_WIDTH)
        self.center(self.addPlaylistWin)

    def center(self, window):
        max_x = self.plane.dim_x()
        max_y = self.plane.dim_y()

        height, width = window.dim_yx()

        new_x = (max_x - width) // 2
        new_y = (max_y - height) // 2

        window.resize_simple(1, 1)
        window.move_yx(new_y, new_x)
        window.resize_simple(height, width)

    def update(self):
        nc.render()



    def initSizes(self):
        global PLAYER_WIDTH, PLAYER_HEIGHT, \
                PLAYLIST_HEIGHT, PLAYLIST_WIDTH, \
                CONTENT_WIDTH, CONTENT_HEIGHT, \
                OPTION_HEIGHT, INFO_HEIGHT, \
                SEARCH_WIDTH, SEARCH_HEIGHT

        max_x = self.plane.dim_x()
        max_y = self.plane.dim_y()

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
        pass

    def resize(self):
        pass
