from mpd import MPDClient

class PlayerDead(Exception):
    pass

class Player:

    def __init__(self):

        self.client = MPDClient()
        self.client.timeout = 10
        self.client.connect("localhost", 6600)

    def play(self, url: str):
        id = self.client.addid(url)
        self.client.playid(id)

    def pause(self):
        is_paused = self.client.status()["state"] == "pause"
        self.client.pause(0 if is_paused else 1)

    def stop(self):
        self.client.stop()

    def quit(self):
        self.client.close()
        self.client.disconnect()

    def seek(self, time: int):
        self.client.seekcur(time)

    def seek_percent(self, percent):
        duration = self.client.status()["duration"]
        self.seek(duration * percent)

    def get_property(self, prop: str, default):
        properties = self.client.status()
        try:
            return properties[prop]
        except KeyError:
            return default

    def get_time(self, default=0):
        return float(self.get_property("elapsed", default))

    def get_duration(self, default=0):
        return float(self.get_property("duration", default))

    def set_repeat(self, state: bool):
        self.client.repeat(1 if state else 0)

    def set_volume(self, vol: int):
        self.client.setvol(vol)

    def check_alive(self):
        if True:
            pass
        raise PlayerDead

    def is_playing(self):
        return self.get_property("state", "stop") == "stop"

    def is_song_finished(self):
        return self.get_property("state", "") == "stop"

