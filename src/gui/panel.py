from gui import screen
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
        return max(round(self.screen.max_x * self._width / 100), self.min_width)
        # TODO : handle absolute mode

    @width.setter
    def width(self, new_val):
        self._width = new_val
        self.resize()
        # TODO : trigger resize

    @property
    def height(self):
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
        self.set_left_to(self.left_to)
        self.set_right_to(self.right_to)
        self.set_above_of(self.above_of)
        self.set_below_of(self.below_of)

    def draw_box(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def set_right_to(self, right_to):
        if not right_to:
            return
        self.right_to.append(right_to)
        right_to.left_to.append(self)

        self.x = max(self.x, right_to.x + right_to.width)

    def set_left_to(self, left_to):
        if not left_to:
            return
        self.left_to.append(left_to)
        left_to.right_to.append(self)

    def set_above_of(self, above_of):
        if not above_of:
            return
        self.above_of.append(above_of)
        above_of.below_of.append(self)

    def set_below_of(self, below_of):
        if not below_of:
            return
        self.below_of.append(below_of)
        below_of.above_of.append(self)

        self.y = max(self.y, below_of.y + below_of.height)

    def center(self):
        max_x = self.screen.max_x
        max_y = self.screen.max_y

        new_x = (max_x - self.width) // 2
        new_y = (max_y - self.height) // 2

        self.win.mvwin(new_y, new_x)
