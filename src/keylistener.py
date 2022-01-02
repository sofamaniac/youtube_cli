from pynput import keyboard
import sys

app = None


class Listener:
    def __init__(self, application):
        global app
        app = application
        self.keys_down = set()
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )

    def checkShortcut(self):
        if "media_next" in self.keys_down:
            app.next()
        if "media_previous" in self.keys_down:
            app.prev()
        if "media_play_pause" in self.keys_down:
            app.pause()

    def on_press(self, key):
        try:
            k = key.char  # single-char keys
        except:
            k = key.name  # other keys
        self.keys_down.add(k)
        self.checkShortcut()

    def on_release(self, key):
        try:
            k = key.char  # single-char keys
        except:
            k = key.name  # other keys
        if k in self.keys_down:
            self.keys_down.remove(k)

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()


if __name__ == "__main__":
    listener = keyboard.Listener(on_press=lambda x: print(x))
    listener.start()
    while True:
        continue
