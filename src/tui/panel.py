from tui import screen
import curses

RELATIVE_MODE = "relative"  # in % of the screen dimensions
ABSOLUTE_MODE = "absolute"  # in absolute number of cells


class Panel:
    def __init__(
        self,
        x=0,
        y=0,
        width=0,
        height=0,
        min_width=0,
        min_height=0,
        w_mode=RELATIVE_MODE,
        h_mode=RELATIVE_MODE,
        right_to=None,
        left_to=None,
        below_of=None,
        above_of=None,
        screen=None,
    ):

        self._x = x
        self._y = y

        self._width = width
        self._height = height

        self.min_width = min_width
        self.min_height = min_height

        self.width_mode = w_mode
        self.height_mode = h_mode

        self.right_to = []
        self.left_to = []
        self.below_of = []
        self.above_of = []

        self.set_right_to(right_to)
        self.set_left_to(left_to)
        self.set_above_of(above_of)
        self.set_below_of(below_of)

        self.screen = screen

        self.win = self.screen.add_win(y, x, self.height, self.width)

    @property
    def width(self):
        if self.width_mode == ABSOLUTE_MODE:
            return self._width
        else:
            return max(round(self.screen.max_x * self._width / 100), self.min_width)

    @width.setter
    def width(self, new_val):
        self._width = new_val
        self.resize()

    @property
    def height(self):
        if self.height_mode == ABSOLUTE_MODE:
            return self._height
        else:
            return max(round(self.screen.max_y * self._height / 100), self.min_height)

    @height.setter
    def height(self, new_val):
        self._height = new_val
        self.resize()

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new_val):
        self._x = new_val
        self.win.mvwin(self.y, self.x)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, new_val):
        self._y = new_val
        self.win.mvwin(self.y, self.x)

    def resize(self, new_w=None, new_h=None):
        """Resize the panel to the given dimension"""

        self._width = self._width if new_w is None else new_w
        self._height = self._height if new_h is None else new_h

        self.win.resize(self.height, self.width)
        for r in self.right_to:
            self.set_right_to(r)
        for l in self.left_to:
            self.set_left_to(l)
        for b in self.below_of:
            self.set_below_of(b)
        for a in self.above_of:
            self.set_above_of(a)

    def draw_box(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def set_right_to(self, right_to):
        if not right_to:
            return

        if right_to not in self.right_to:
            self.right_to.append(right_to)
            right_to.left_to.append(self)

        new_x = max([r.x + r.width for r in self.right_to])
        if new_x + self.width > self.screen.max_x:
            self.x = self.screen.max_x - self.height
        else:
            self.x = new_x

    def set_left_to(self, left_to):
        if not left_to:
            return
        if left_to not in self.left_to:
            self.left_to.append(left_to)
            left_to.right_to.append(self)

    def set_above_of(self, above_of):
        if not above_of:
            return
        if above_of not in self.above_of:
            self.above_of.append(above_of)
            above_of.below_of.append(self)

    def set_below_of(self, below_of):
        if not below_of:
            return
        if below_of not in self.below_of:
            self.below_of.append(below_of)
            below_of.above_of.append(self)

        new_y = max([b.y + b.height for b in self.below_of])
        if new_y + self.height > self.screen.max_y:
            self.y = self.screen.max_y - self.height
        else:
            self.y = new_y

    def center(self):
        max_x = self.screen.max_x
        max_y = self.screen.max_y

        new_x = (max_x - self.width) // 2
        new_y = (max_y - self.height) // 2

        self.win.mvwin(new_y, new_x)
