"""This module provide a class that links keyboard event to actions"""

import curses
from gui.screen import Directions


class KeyConfiguration:
    """Class that contains all the (key, command)"""

    def __init__(self, app):

        self.actions = {
            "q": [quit],
            "j": [app.select, Directions.DOWN],
            "k": [app.select, Directions.UP],
            "h": [app.select, Directions.LEFT],
            "l": [app.select, Directions.RIGHT],
            " ": [app.pause],
            ">": [app.next],
            "<": [app.prev],
            "m": [app.toggleMute],
            "f": [app.increaseVolume, 5],
            "d": [app.increaseVolume, -5],
            "n": [app.nextPage],
            "p": [app.prevPage],
            "\n": [app.enter],
            "a": [app.setPlaylist],
            "r": [app.toggleRepeat],
            "y": [app.toggleShuffle],
            "t": [app.addToPlaylist],
            "s": [app.search],
            "c": [app.reload],
            "v": [app.toggleVideo],
            curses.KEY_LEFT: [app.forward, -5],
            curses.KEY_RIGHT: [app.forward, 5],
            "à": [app.seekPercent, 0],
            "&": [app.seekPercent, 10],
            "é": [app.seekPercent, 20],
            '"': [app.seekPercent, 30],
            "'": [app.seekPercent, 40],
            "(": [app.seekPercent, 50],
            "-": [app.seekPercent, 60],
            "è": [app.seekPercent, 70],
            "_": [app.seekPercent, 80],
            "ç": [app.seekPercent, 90],
            ":": [app.command],
        }

    def check_action(self, keycode):
        """Given a keycode, check if there is an action bind to it,
        and if so runs it"""
        if keycode in self.actions:
            action = self.actions[keycode][0]
            args = self.actions[keycode][1:]
            action(*args)

    def add_action(self, key, action, args):
        """Add a binding of action(args) to [key]"""
        self.actions[key] = [action, *args]
