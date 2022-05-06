"""Module providing basic panel components for the program"""

import curses
from gui.screen import CurseString, Directions, PanelDirections
from gui import screen, panel


class Widget(panel.Panel):
    """Basic component of the interface"""

    def __init__(
        self,
        title,
        x,
        y,
        width,
        height,
        min_width=0,
        min_height=0,
        right_to=None,
        left_to=None,
        below_of=None,
        above_of=None,
        screen=None,
    ):

        panel.Panel.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            min_width=min_width,
            min_height=min_height,
            right_to=right_to,
            left_to=left_to,
            below_of=below_of,
            above_of=above_of,
            screen=screen,
        )

        self.source = None
        self.selected = 0
        self.title = CurseString(title)
        self.title.set_attr(curses.A_BOLD)
        self.page = 0
        self.visible = True
        self.selectable = True

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

        if len(to_display) > page_size:
            to_display = to_display[:page_size]

        for i, s in enumerate(to_display):
            if self.selectable and i + off == self.selected and draw_select:
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

        if not self.selectable:
            return
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
        if self.selected + self.get_page_size() <= self.source.get_max_index():
            self.page += 1
            self.selected = self.selected + self.get_page_size()

    def prev_page(self):
        page_incr = max(0, self.page - 1) - self.page
        self.page += page_incr
        self.selected += self.get_page_size() * page_incr

    def get_next_selectable_neighbour(self, direction):
        next = None
        match direction:
            case PanelDirections.UP:
                next = self.below_of
            case PanelDirections.DOWN:
                next = self.above_of
            case PanelDirections.LEFT:
                next = self.right_to
            case PanelDirections.RIGHT:
                next = self.left_to

        if next and next.selectable:
            return next
        elif next:
            return next.get_next_selectable_neighbour(direction)
        else:
            return next
