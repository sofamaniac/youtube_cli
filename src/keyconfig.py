import curses
from gui.screen import Directions

class KeyConfiguration:
    def __init__(self, app):

        self.actions = {
            "q": [quit],

            "j": [app.select, Directions.Down],
            "k": [app.select, Directions.Up],
            "h": [app.select, Directions.Left],
            "l": [app.select, Directions.Right],

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

            "0": [app.seekPercent, 0],
            "1": [app.seekPercent, 10],
            "2": [app.seekPercent, 20],
            "3": [app.seekPercent, 30],
            "4": [app.seekPercent, 40],
            "5": [app.seekPercent, 50],
            "6": [app.seekPercent, 60],
            "7": [app.seekPercent, 70],
            "8": [app.seekPercent, 80],
            "9": [app.seekPercent, 90],

            ":": [app.command]
        }

        #self.setupConfig()

    def setupConfig(self):
        actions = {}
        for key in self.actions.keys():
            if type(key) is str:
                actions[ord(key)] = self.actions[key]
            else:
                actions[key] = self.actions[key]
        self.actions = actions

    def checkAction(self, keycode):
        if keycode in self.actions.keys():
            f = self.actions[keycode][0]
            args = self.actions[keycode][1:]
            f(*args)

