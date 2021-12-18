import curses
import curses.ascii

class Textbox():
    def __init__(self, win):
        self.win = win
        self.content = []
        self.editingpos = 0
        

    def edit(self):
        while True:
            c = self.win.getch()

            if c == curses.ascii.BEL or c == curses.ascii.NL:
                self.win.clear()
                self.win.refresh()
                return 0
            elif c == curses.KEY_BACKSPACE or c == curses.ascii.BS:
                self.content.pop(self.editingpos)
            elif c == curses.KEY_LEFT:
                self.editingpos -= 1
                self.editingpos = max(0, self.editingpos)
            elif c == curses.KEY_RIGHT:
                self.editingpos += 1
                self.editingpos = min(len(self.content), self.editingpos)
            elif curses.ascii.isprint(c) and len(self.content) < self.win.getmaxyx()[1]-1:
                self.content.append(curses.keyname(c).decode())

            self.win.clear()
            self.win.addstr(0, 0, ''.join(self.content))
            self.win.refresh()

    def gather(self):
        return ''.join(self.content)

    def reset(self):
        self.content = []
