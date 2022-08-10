from mpd import MPDClient
from mpv import MPV
from mpv import ShutdownError as MPVDeadError
from typing import Optional


class PlayerDeadError(Exception):
    pass


class Player:
    pass


class AudioPlayerMPD(Player):
    def __init__(self):

        self.client = MPDClient()
        self.client.timeout = 10
        self.client.connect("localhost", 6600)

    def play(self, url: str):
        file_id = self.client.addid(url)
        self.client.playid(file_id)

    def pause(self, b: Optional[bool] = None):
        is_paused = self.client.status()["state"] == "pause"
        target = b if b is not None else is_paused
        self.client.pause(0 if target else 1)

    def stop(self):
        self.client.stop()

    def quit(self):
        self.client.stop()
        self.client.close()
        self.client.disconnect()

    def seek(self, dt: int):
        if dt >= 0:
            dt = "+" + str(dt)
        else:
            dt = str(dt)
        self.client.seekcur(dt)

    def seek_percent(self, percent):
        self.client.seekcur(self.duration * percent / 100)

    def get_property(self, prop: str, default):
        properties = self.client.status()
        try:
            return properties[prop]
        except KeyError:
            return default

    @property
    def time(self):
        return float(self.get_property("elapsed", 0))

    @property
    def duration(self):
        return float(self.get_property("duration", 0))

    def set_repeat(self, state: str):
        if state == "No":
            self.client.repeat(0)
        elif state == "Song":
            self.client.repeat(1)

    def set_volume(self, vol: int):
        self.client.setvol(vol)

    def check_alive(self):
        return True

    def is_playing(self):
        return self.get_property("state", "stop") != "stop"

    def is_song_finished(self):
        return self.get_property("state", "") == "stop"


class VideoPlayer(Player):
    def __init__(self, video="auto"):
        self.player = MPV(video=video, ytdl=True)

    def play(self, url):
        self.player.play(url)

    def stop(self):
        self.player.stop()

    def pause(self, b: Optional[bool] = None):
        if b is not None:
            self.player.pause = b
        else:
            self.player.pause = not self.player.pause

    def set_repeat(self, state):
        if state == "Song":
            self.player.loop_file = "inf"
        else:
            self.player.loop_file = "no"

    def set_volume(self, vol):
        self.player.volume = vol

    def check_alive(self):
        try:
            self.player.check_core_alive()
        except MPVDeadError:
            raise PlayerDeadError from MPVDeadError

    def is_playing(self):
        return self.player.media_title

    @property
    def duration(self):
        return self.player.duration

    @property
    def time(self):
        return self.player.time_pos

    def seek(self, dt, mode="relative"):
        self.player.command("seek", f"{dt}", mode)

    def seek_percent(self, dt):
        self.player.command("seek", f"{dt}", "absolute-percent")

    def quit(self):
        self.stop()
        del self.player

    def is_song_finished(self):
        return not self.is_playing()


class AudioPlayer(VideoPlayer):
    def __init__(self):
        VideoPlayer.__init__(self, video=False)
