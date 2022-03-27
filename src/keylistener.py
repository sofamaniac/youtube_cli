"""Module to capture key event globally"""
from pynput import keyboard

class Listener:
    """This class listen in permanence to check if media keys are used"""
    def __init__(self, application):
        self.app = application
        self.keys_down = set()
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )

    def check_shortcut(self):
        """This function check if a media key is pressed and if so
        does the appropriate actions"""
        if "media_next" in self.keys_down:
            self.app.next()
        if "media_previous" in self.keys_down:
            self.app.prev()
        if "media_play_pause" in self.keys_down:
            self.app.pause()

    def on_press(self, key):
        """Handle key presses and check if actions should be taken"""
        try:
            k = key.char  # single-char keys
        except AttributeError:
            k = key.name  # other keys
        self.keys_down.add(k)
        self.check_shortcut()

    def on_release(self, key):
        """Handle key releases"""
        try:
            k = key.char  # single-char keys
        except AttributeError:
            k = key.name  # other keys
        if k in self.keys_down:
            self.keys_down.remove(k)

    def start(self):
        """Start the listener"""
        self.listener.start()

    def stop(self):
        """Stop the listener"""
        self.listener.stop()


if __name__ == "__main__":
    listener = keyboard.Listener(on_press=print)
    listener.start()
    while True:
        continue
