import asyncio
from typing import Optional
from threading import Thread
from mpris_server.server import Server
from mpris_server.events import EventAdapter
from mpris_server.adapters import (
    Metadata,
    PlayState,
    MprisAdapter,
    Microseconds,
    VolumeDecimal,
    RateDecimal,
    PlayerAdapter,
    RootAdapter,
    ActivePlaylist,
)
from mpris_server.base import URI, MIME_TYPES, DEFAULT_RATE, DbusObj, Track
from mpris_server.mpris.metadata import MetadataObj
from mpris_server.mpris.compat import get_track_id
from application import Application
import logging

log = logging.getLogger(__name__)


class Adapter(MprisAdapter):
    def __init__(self, app: Application):
        self.app = app
        super().__init__()

    def can_go_next(self) -> bool:
        return True

    def can_go_previous(self) -> bool:
        return self.app.in_playlist and self.app.playlist.current_index > 0

    def can_play(self):
        return True

    def can_pause(self) -> bool:
        return True

    def can_seek(self) -> bool:
        return True

    def can_control(self) -> bool:
        return True

    def get_current_position(self) -> Microseconds:
        time = self.app.player.time
        time = time if time else 0
        return time * 10**6

    def next(self):
        asyncio.run(self.app.next())

    def previous(self):
        asyncio.run(self.app.prev())

    def pause(self):
        asyncio.run(self.app.pause(True))

    def resume(self):
        asyncio.run(self.app.pause(False))

    def stop(self):
        asyncio.run(self.app.stop())

    def play(self):
        asyncio.run(self.app.start())

    def get_playstate(self) -> PlayState:
        if self.app.is_playing():
            return PlayState.PLAYING
        return PlayState.PAUSED

    def seek(self, time: Microseconds, track_id: Optional[DbusObj] = None):
        asyncio.run(self.app.seek(time))

    def open_uri(self, uri: str):
        self.app.open_uri(uri)

    def is_repeating(self) -> bool:
        return self.app.repeat == "Song"

    def is_playlist(self) -> bool:
        return self.app.in_playlist

    def get_rate(self) -> RateDecimal:
        return 1

    def set_rate(self, val: RateDecimal):
        pass

    def get_shuffle(self) -> bool:
        return self.app.shuffled

    async def _set_shuffle(self, val: bool):
        self.app.shuffled = val

    def set_shuffle(self, val: bool):
        asyncio.run(self._set_shuffle(val))

    def get_art_url(self, track: int = None) -> str:
        # return self.app.get_art_url(track)
        return ""

    # according to mpris doc, val is a float between 0 and 1
    def get_volume(self) -> VolumeDecimal:
        return self.app.volume / 100

    def set_volume(self, val: VolumeDecimal):
        self.app.volume = int(max(0, val * 100))

    def is_mute(self) -> bool:
        return self.app.muted

    def set_mute(self, val: bool):
        self.app.muted = val

    def get_stream_title(self) -> str:
        return self.app.playing.title

    def get_duration(self) -> Microseconds:
        return self.app.player.duration

    def metadata(self) -> Metadata:
        current = self.app.playing
        return MetadataObj(
            track_id=get_track_id(current.title),
            length=self.app.player.duration,
            url=current.mpris_url(),
            artists=["unknown"],
            title=current.title,
        )

    def get_current_track(self) -> Track:
        return Track()

    def add_track(self, uri: str, after_track: DbusObj, set_as_current: bool):
        pass

    def can_edit_track(self) -> bool:
        return False

    def set_repeating(self, val: bool):
        pass

    def set_loop_status(self, val: str):
        pass

    def get_previous_track(self) -> Track:
        return Track()

    def get_next_track(self) -> Track:
        return Track()

    def get_active_playlist(self) -> ActivePlaylist:
        return (False, ("/", "", ""))


class CustomEventAdapter(EventAdapter):
    def on_app_event(self, event: str):
        # events = ["play", "pause", "stop", "prev", "next", "shuffle", "repeat", "volume"]

        if event in ["pause", "play"]:
            self.on_playpause()
        elif event == "volume":
            self.on_volume()


def initialize(app):
    adapter = Adapter(app)
    mpris = Server("youtube_cli", adapter=adapter)
    mpris.publish()
    log.info("MPRIS server published")

    app.event_handler = CustomEventAdapter(root=mpris.root, player=mpris.player)

    thread = Thread(target=mpris.loop, daemon=True)
    thread.start()
    log.info("MPRIS thread started")
