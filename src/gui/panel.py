from gui import screen
import curses
import _curses

RELATIVE_MODE = "relative"  # in % of the screen dimensions
ABSOLUTE_MODE = "absolute"  # in absolute number of cells


class Panel:
    def __init__(
        self,
        x=0,
        y=0,
        width=0,
        height=0,
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

        self.width_mode = w_mode
        self.height_mode = h_mode

        self.right_to = right_to
        self.left_to = left_to
        self.below_of = below_of
        self.above_of = above_of

        self.set_right_to(right_to)
        self.set_left_to(left_to)
        self.set_above_of(above_of)
        self.set_below_of(below_of)

        self.screen = screen

        self.win = self.screen.add_win(y, x, self.height, self.width)

    @property
    def width(self):
        return int(self.screen.max_x * self._width / 100)
        # TODO : handle absolute mode

    @width.setter
    def width(self, new_val):
        self._width = new_val
        self.resize()
        # TODO : trigger resize

    @property
    def height(self):
        return int(self.screen.max_y * self._height / 100)

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

        self._width = self.width if new_w is None else new_w
        self._height = self.height if new_h is None else new_h

        self.win.resize(self.height, self.width)
        self.set_left_to(self.left_to)
        self.set_above_of(self.above_of)

    def draw_box(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def set_right_to(self, right_to):
        self.right_to = right_to
        if not right_to:
            return
        right_to.left_to = self

        self.x = right_to.x + right_to.width

    def set_left_to(self, left_to):
        self.left_to = left_to
        if not left_to:
            return
        left_to.right_to = self

    def set_above_of(self, above_of):
        self.above_of = above_of
        if not above_of:
            return
        above_of.below_of = self

    def set_below_of(self, below_of):
        self.below_of = below_of
        if not below_of:
            return
        below_of.above_of = self

        self.y = below_of.y + below_of.height
