import curses
import curses.ascii


class Textbox:
    def __init__(self, win):
        self.win = win
        self.win.keypad(
            True
        )  # needed to interpret special keys such as arrows and backspace
        self.content = []
        self.editingpos = -1  # position of the letter right in front of the cursor

    def edit(self):
        while True:
            c = self.win.getch()

            if c == curses.ascii.BEL or c == curses.ascii.NL:
                self.win.clear()
                self.win.refresh()
                return 0
            elif c == curses.KEY_BACKSPACE or c == curses.ascii.BS:
                if len(self.content) > 0:
                    self.content.pop(self.editingpos)
                    self.editingpos -= 1
            elif c == curses.KEY_LEFT:
                self.editingpos -= 1
                self.editingpos = max(0, self.editingpos)
            elif c == curses.KEY_RIGHT:
                self.editingpos += 1
                self.editingpos = min(len(self.content), self.editingpos)
            elif (
                curses.ascii.isprint(c)
                and len(self.content) < self.win.getmaxyx()[1] - 1
            ):
                self.editingpos += 1
                if self.content:
                    self.content.insert(self.editingpos, curses.keyname(c).decode())
                else:
                    self.content.append(curses.keyname(c).decode())
            if c == curses.ascii.ESC:
                self.reset()
                break

            self.win.clear()
            if 0 <= self.editingpos < len(self.content) - 1:
                # the char right after the cursor is highlighted
                self.win.addstr(0, 0, "".join(self.content))
                self.win.addstr(
                    0,
                    self.editingpos + 1,
                    self.content[self.editingpos + 1],
                    curses.A_STANDOUT,
                )
            else:  # if content is empty or the cursor is after content (ie where inputting at the end)
                self.win.addstr(0, 0, "".join(self.content) + "\u2588")
            self.win.refresh()

    def gather(self):
        return "".join(self.content)

    def reset(self):
        self.content = []
        self.editingpos = -1
