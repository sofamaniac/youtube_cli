"""This module provide a class that links keyboard event to actions"""

import curses
from tui.screen import Directions, PanelDirections


class KeyConfiguration:
    """Class that contains all the (key, command)"""

    def __init__(self, app):

        self.actions = {
            "q": [quit],
            "j": [app.select, Directions.DOWN],
            "k": [app.select, Directions.UP],
            "h": [app.select, Directions.LEFT],
            "l": [app.select, Directions.RIGHT],
            "J": [app.select, PanelDirections.DOWN],
            "K": [app.select, PanelDirections.UP],
            "H": [app.select, PanelDirections.LEFT],
            "L": [app.select, PanelDirections.RIGHT],
            "g": [app.jump_to_current_playing],
            " ": [app.pause],
            ">": [app.next],
            "<": [app.prev],
            "m": [app.toggle_mute],
            "f": [app.increase_volume, 5],
            "d": [app.increase_volume, -5],
            "n": [app.next_page],
            "p": [app.prev_page],
            "a": [app.set_playlist],
            "r": [app.toggle_repeat],
            "y": [app.toggle_shuffle],
            "t": [app.add_to_playlist],
            "s": [app.search],
            "c": [app.reload],
            "v": [app.toggle_video],
            "à": [app.seek_percent, 0],
            "&": [app.seek_percent, 10],
            "é": [app.seek_percent, 20],
            '"': [app.seek_percent, 30],
            "'": [app.seek_percent, 40],
            "(": [app.seek_percent, 50],
            "-": [app.seek_percent, 60],
            "è": [app.seek_percent, 70],
            "_": [app.seek_percent, 80],
            "ç": [app.seek_percent, 90],
            ":": [app.command],
            "\n": [app.enter],
            curses.KEY_LEFT: [app.forward, -5],
            curses.KEY_RIGHT: [app.forward, 5],
            curses.ascii.ESC: [app.escape],
        }

    async def check_action(self, keycode):
        """Given a keycode, check if there is an action bind to it,
        and if so runs it"""

        if keycode in self.actions:
            action = self.actions[keycode][0]
            args = self.actions[keycode][1:]
            await action(*args)

        if isinstance(keycode, str) and ord(keycode) in self.actions:
            code = ord(keycode)
            action = self.actions[code][0]
            args = self.actions[code][1:]
            await action(*args)

    def add_action(self, key, action, args):
        """Add a binding of action(args) to [key]"""
        self.actions[key] = [action, *args]
