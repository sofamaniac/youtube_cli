import curses
import curses.ascii
import _curses

class Textbox:
    def __init__(self, win):
        self.win = win
        self.win.keypad(True)  # needed to interpret special keys such as arrows and backspace
        self.content = ['\0']
        self.editingpos = 0  # position of the letter right in front of the cursor

    def edit(self, update=None):
        """the update parameter is an optional function to be called to update the screen while
        the process is occupied by the search box"""
        self.win.refresh()
        size = self.win.getmaxyx()[1] - 2
        while True:
            try:
                c = self.win.get_wch()
            except _curses.error:
                continue

            if type(c) is int:
                if c == -1:
                    continue
                if c == curses.ascii.ESC:
                    self.reset()
                    return
                if c == curses.ascii.BEL or c == curses.ascii.NL:
                    return
                elif c == curses.KEY_DC or c == curses.KEY_BACKSPACE or c == curses.ascii.BS:
                    if len(self.content) > 0:
                        self.content.pop(self.editingpos)
                        self.editingpos -= 1
                elif c == curses.KEY_LEFT:
                    self.editingpos -= 1
                    self.editingpos = max(0, self.editingpos)
                elif c == curses.KEY_RIGHT:
                    self.editingpos += 1
                    self.editingpos = min(len(self.content)-1, self.editingpos)
            else:
                if c == '\n':
                    return
                elif ord(c) == curses.ascii.ESC:  # may break other function keys
                    self.reset()
                    return
                self.editingpos += 1
                self.content.insert(self.editingpos, c)

            if update:
                update()

            self.win.erase()

            # as the text may be too long to fit, 
            # we make sure the cursor is on screen
            # ie the text scroll with the cursors
            beg = max(0, self.editingpos+1-size)
            end = min(len(self.content), beg + size + 1)

            str_to_show = self.gather()[beg:end]

            if 0 <= self.editingpos < len(self.content) - 1:
                # the char right after the cursor is highlighted
                self.win.addstr(0, 0, str_to_show)
                self.win.addch(
                    0,
                    self.editingpos - beg,
                    self.content[self.editingpos+1],
                    curses.A_STANDOUT,
                )
            else:  # if content is empty or the cursor is after content (ie where inputting at the end)
                self.win.addstr(0, 0, str_to_show + "\u2588")

            self.win.refresh()

    def gather(self):
        return "".join(self.content[1:])

    def reset(self):
        self.content = ['\0']
        self.editingpos = 0
