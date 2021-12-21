import curses
import curses.ascii

class Textbox():
    def __init__(self, win):
        self.win = win
        self.content = []
        self.editingpos = -1
        

    def edit(self):
        # TODO find a good way of handling keycode (kitty is apparently using a non standard protocol)
        while True:
            c = self.win.getch()

            if c == curses.ascii.BEL or c == curses.ascii.NL:
                self.win.clear()
                self.win.refresh()
                return 0
            elif c == 127 or c == curses.KEY_BACKSPACE or c == curses.ascii.BS:
                if len(self.content) > 0:
                    self.content.pop(self.editingpos)
                    self.editingpos -= 1
            elif c == curses.ascii.STX or c == curses.KEY_LEFT:
                self.editingpos -= 1
                self.editingpos = max(0, self.editingpos)
            elif c == curses.KEY_RIGHT:
                self.editingpos += 1
                self.editingpos = min(len(self.content), self.editingpos)
            elif curses.ascii.isprint(c) and len(self.content) < self.win.getmaxyx()[1]-1:
                self.content.append(curses.keyname(c).decode())
                self.editingpos += 1
            if c == curses.ascii.ESC:
                self.reset()
                break

            self.win.clear()
            self.win.addstr(0, 0, ''.join(self.content) + '\u258F')
            self.win.refresh()

    def gather(self):
        return ''.join(self.content)

    def reset(self):
        self.content = []
        self.editingpos = -1
