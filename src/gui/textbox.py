"""Module that (re)implement some input boxes for curses"""
import curses
import curses.ascii
import _curses
from gui import panel


class Textbox(panel.Panel):
    """Input box"""

    def __init__(self, *args, **kwargs):
        super(Textbox, self).__init__(*args, **kwargs)
        self.win.keypad(
            True
        )  # needed to interpret special keys such as arrows and backspace
        self.content = ["\0"]
        self.editingpos = 0  # position of the letter right in front of the cursor

    def edit(self, update=None):
        """the update parameter is an optional function to be called to update the screen while
        the process is occupied by the search box"""
        self.win.refresh()
        size = self.win.getmaxyx()[1] - 2
        while True:
            try:
                char = self.win.get_wch()
            except _curses.error:
                continue

            if isinstance(char, int):
                if char == -1:
                    continue
                elif char == curses.ascii.ESC:
                    self.reset()
                    return
                elif char in [curses.ascii.BEL, curses.ascii.NL]:
                    return
                elif (
                    char in [curses.KEY_DC, curses.KEY_BACKSPACE, curses.ascii.BS]
                    and len(self.content) > 0
                ):
                    self.content.pop(self.editingpos)
                    self.editingpos -= 1
                elif char == curses.KEY_LEFT:
                    self.editingpos -= 1
                    self.editingpos = max(0, self.editingpos)
                elif char == curses.KEY_RIGHT:
                    self.editingpos += 1
                    self.editingpos = min(len(self.content) - 1, self.editingpos)
            else:
                if char == "\n":
                    return
                elif ord(char) == curses.ascii.ESC:  # may break other function keys
                    self.reset()
                    return
                self.editingpos += 1
                self.content.insert(self.editingpos, char)

            if update:
                update()

            self.win.erase()

            # as the text may be too long to fit,
            # we make sure the cursor is on screen
            # ie the text scroll with the cursors
            beg = max(0, self.editingpos + 1 - size)
            end = min(len(self.content), beg + size + 1)

            str_to_show = self.gather()[beg:end]

            if 0 <= self.editingpos < len(self.content) - 1:
                # the char right after the cursor is highlighted
                self.win.addstr(0, 0, str_to_show)
                self.win.addch(
                    0,
                    self.editingpos - beg,
                    self.content[self.editingpos + 1],
                    curses.A_STANDOUT,
                )
            else:  # if content is empty or the cursor is after content (ie inputting at the end)
                self.win.addstr(0, 0, str_to_show + "\u2588")

            self.win.refresh()

    def gather(self):
        """Return the string currently in the input box"""
        return "".join(self.content[1:])

    def reset(self):
        """ "Reset the input box to its original state"""
        self.content = ["\0"]
        self.editingpos = 0
