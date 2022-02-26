from mpd import MPDClient
from mpv import MPV
from mpv import ShutdownError as MPVDeadError

class PlayerDeadError(Exception):
    pass

class AudioPlayer:

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

    def seek(self, dt: int):
        if dt >= 0:
            dt = '+' + str(dt)
        else:
            dt = str(dt)
        self.client.seekcur(dt)

    def seek_percent(self, percent):
        duration = self.get_duration()
        self.client.seekcur(duration * percent / 100)

    def get_property(self, prop: str, default):
        properties = self.client.status()
        try:
            return properties[prop]
        except KeyError:
            return default

    @property
    def time(self, default=0):
        return float(self.get_property("elapsed", default))

    @property
    def duration(self, default=0):
        return float(self.get_property("duration", default))

    def set_repeat(self, state: str):
        if state == "No":
            self.client.repeat(0)
        elif state == "Song":
            self.client.repeat(1)

    def set_volume(self, vol: int):
        self.client.setvol(vol)

    def check_alive(self):
        if True:
            return
        raise PlayerDeadError

    def is_playing(self):
        return self.get_property("state", "stop") != "stop"

    def is_song_finished(self):
        return self.get_property("state", "") == "stop"

class VideoPlayer:

    def __init__(self):
        self.player = MPV(video="auto", ytdl=True)

    def play(self, url):
        self.player.play(url)

    def stop(self):
        self.player.stop

    def pause(self):
        self.player.command("cycle", "pause")

    def set_repeat(self, state):
        if state == "Song":
            self.player.loop_file = "inf"
        elif state == "No":
            self.player.loop_file = "no"

    def set_volume(self, vol):
        self.player.volume = vol

    def check_alive(self):
        try:
            self.player.check_core_alive()
        except MPVDeadError:
            raise PlayerDeadError

    def is_playing(self):
        return self.player.media_title != ""

    @property
    def duration(self):
        return self.player.duration

    @property
    def time(self):
        return self.player.time_pos

    def seek(self, dt):
        self.player.command("seek", f"{dt}", "relative")

    def seek_percent(self, dt):
        self.player.command("seek", f"{dt}", "absolute-percent")

    def quit(self):
        del self.player

    def is_song_finished(self):
        return not self.is_playing()
