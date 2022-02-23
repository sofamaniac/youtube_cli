
from gui.screen import CurseString, Directions
import gui.screen as screen
import curses

class Panel:
    def __init__(self, win, title):
        self.source = None
        self.selected = 0
        self.win = win
        self.title = CurseString(title)
        self.title.setAttr(curses.A_BOLD)
        self.page = 0
        self.visible = True

    def drawBox(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def update(self, drawSelect=True, to_display=[]):
        if not self.visible:
            return

        page_size = self.getPageSize()
        self.win.erase()
        self.drawBox()

        off = self.page * page_size
        width = self.win.getmaxyx()[1]-2

        self.title.drawToWin(self.win, 0, 1, width) 

        if not to_display and self.source:
            to_display = self.getContent(off, page_size + off)

        for i in range(len(to_display)):
            if i + off == self.selected and drawSelect:
                to_display[i].setAttr(curses.A_STANDOUT)
            to_display[i].drawToWin(self.win, i+1, 1, width)
        self.win.noutrefresh()

    def clear(self, refresh=True):
        self.win.clear()
        if refresh:
            self.win.refresh()

    def toggleVisible(self):
        self.visible = not self.visible
        self.clear()

    def select(self, direction):
        off = self.getPageSize() * self.page
        if direction == Directions.Up:
            self.selected = max(0, self.selected - 1)
            if self.selected < off:
                self.page -= 1
        elif direction == Directions.Down:
            self.selected += 1
            if self.selected > self.source.getMaxIndex():
                self.selected -= 1
            if self.selected >= off + self.getPageSize():
                self.page += 1

    def getSelected(self):
        return self.source.getAtIndex(self.selected)

    def getPageSize(self):
        return self.win.getmaxyx()[0] - 2

    def getContent(self, start, end):
        content = self.source.getItemList(start, end)
        return [CurseString(str(c)) for c in content]

    def next_page(self):
        if self.selected + self.getPageSize() <= self.source.getMaxIndex():
            self.page += 1
            self.selected = self.selected + self.getPageSize()

    def prev_page(self):
        page_incr = max(0, self.page - 1) - self.page
        self.page += page_incr
        self.selected += self.getPageSize() * page_incr
