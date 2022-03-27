"""Module providing basic panel components for the program"""

import curses
from gui.screen import CurseString, Directions
from gui import screen

class Panel:
    """Basic component of the interface"""

    def __init__(self, win, title):
        self.source = None
        self.selected = 0
        self.win = win
        self.title = CurseString(title)
        self.title.set_attr(curses.A_BOLD)
        self.page = 0
        self.visible = True

    def draw_box(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def update(self, draw_select=True, to_display=[]):
        if not self.visible:
            return

        page_size = self.get_page_size()
        self.win.erase()
        self.draw_box()

        off = self.page * page_size
        width = self.win.getmaxyx()[1] - 2

        self.title.draw_to_win(self.win, 0, 1, width)

        if not to_display and self.source:
            to_display = self.get_content(off, page_size + off)

        for i, s in enumerate(to_display):
            if i + off == self.selected and draw_select:
                s.set_attr(curses.A_STANDOUT)
            s.draw_to_win(self.win, i + 1, 1, width)
        self.win.noutrefresh()

    def clear(self, refresh=True):
        self.win.clear()
        if refresh:
            self.win.refresh()

    def toggle_visible(self):
        self.visible = not self.visible
        self.clear()

    def select(self, direction):
        off = self.get_page_size() * self.page
        if direction == Directions.UP:
            self.selected = max(0, self.selected - 1)
            if self.selected < off:
                self.page -= 1
        elif direction == Directions.DOWN:
            self.selected += 1
            if self.selected > self.source.get_max_index():
                self.selected -= 1
            if self.selected >= off + self.get_page_size():
                self.page += 1

    def get_selected(self):
        return self.source.get_at_index(self.selected)

    def get_page_size(self):
        return self.win.getmaxyx()[0] - 2

    def get_content(self, start, end):
        content = self.source.get_item_list(start, end)
        return [CurseString(str(c)) for c in content]

    def next_page(self):
        if self.selected + self.get_page_size() <= self.source.getMaxIndex():
            self.page += 1
            self.selected = self.selected + self.get_page_size()

    def prev_page(self):
        page_incr = max(0, self.page - 1) - self.page
        self.page += page_incr
        self.selected += self.get_page_size() * page_incr
