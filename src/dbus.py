from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next import Variant, DBusError, PropertyAccess
import asyncio
from constants import APP_NAME, PlayerStates, Event

import logging

log = logging.getLogger(__name__)


class RootInterface(ServiceInterface):
    def __init__(self, app):
        name = "org.mpris.MediaPlayer2"
        super().__init__(name)
        self._app = app

    @method()
    def Raise(self):
        pass

    @method()
    def Quit(self):
        quit()

    @dbus_property(access=PropertyAccess.READ)
    def CanQuit(self) -> "b":
        return True

    @dbus_property(PropertyAccess.READ)
    def CanRaise(self) -> "b":
        return False

    @dbus_property(PropertyAccess.READ)
    def HasTrackList(self) -> "b":
        return False

    @dbus_property(PropertyAccess.READ)
    def Identity(self) -> "s":
        return "youtube_cli"

    @dbus_property(PropertyAccess.READ)
    def SupportedUriSchemes(self) -> "as":
        return []

    @dbus_property(PropertyAccess.READ)
    def SupportedMimeTypes(self) -> "as":
        return []  # TODO


class PlayerInterface(ServiceInterface):
    def __init__(self, app):
        name = "org.mpris.MediaPlayer2.Player"
        super().__init__(name)
        self._app = app

    @method()
    async def Next(self):
        await self._app.next()

    @method()
    async def Previous(self):
        await self._app.previous()

    @method()
    async def Pause(self):
        await self._app.pause(b=True)

    @method()
    async def PlayPause(self):
        await self._app.pause()

    @method()
    async def Stop(self):
        await self._app.stop()

    @method()
    async def Play(self):
        await self._app.play()

    @method()
    async def Seek(self, offset: "x"):
        # advance by the time amount given in microsecond
        await self._app.seek(int(offset) / 1e6, mode="relative")

    @method()
    async def SetPosition(self, trackid: "o", position: "x"):
        if (await self._app.playing.get_url()) != trackid:
            return
        self._app.seek(int(position) / 1e6, mode="absolute")

    @method()
    def OpenUri(self, uri: "s"):
        pass

    @signal()
    def Seeked(self) -> "x":
        return self.Position

    @dbus_property(PropertyAccess.READ)
    def PlaybackStatus(self) -> "s":
        if self._app.state == PlayerStates.PAUSED:
            return "Paused"
        elif self._app.state == PlayerStates.PLAYING:
            return "Playing"
        else:
            return "Stopped"

    @dbus_property(PropertyAccess.READ)
    def LoopStatus(self) -> "s":
        if self._app.repeat == "No":
            return "None"
        elif self._app.repeat == "Song":
            return "Track"
        else:
            return "Playlist"

    @dbus_property()
    def Rate(self) -> "d":
        return 1.0

    @Rate.setter
    def Rate_setter(self, val: "d"):
        pass

    @dbus_property()
    def Shuffle(self) -> "b":
        return self._app.shuffled

    @Shuffle.setter
    def Shuffle_setter(self, val: "b"):
        self._app.shuffled = val
        self.emit_properties_changed({"Shuffle": self._app.shuffled})

    @dbus_property(PropertyAccess.READ)
    def Metadata(self) -> "a{sv}":
        current = self._app.playing
        url = f"https://youtu.be/{current.id}"
        duration = self._app.player.duration
        duration = int(duration * 1e6) if duration else 0
        return {
            "mpris:trackid": Variant("o", "/org/mpris/MediaPlayer2/youtube_cli"),
            "mpris:duration": Variant("x", duration),
            "xesam:title": Variant("s", current.title),
            "xesam:url": Variant("s", url),
        }

    @dbus_property()
    def Volume(self) -> "d":
        vol = self._app.volume / 100
        return vol

    @Volume.setter
    def Volume_setter(self, val: "d"):
        self._app.volume = max(0, int(val * 100))
        self.emit_properties_changed({"Volume": self._app.volume / 100})

    @dbus_property(PropertyAccess.READ)
    def Position(self) -> "x":
        time = self._app.player.time
        time = time if time is not None else 0
        return int(time * 1e6)

    @dbus_property(PropertyAccess.READ)
    def MinimumRate(self) -> "d":
        return 0.0

    @dbus_property(PropertyAccess.READ)
    def MaximumRate(self) -> "d":
        return 1.0

    @dbus_property(PropertyAccess.READ)
    def CanGoNext(self) -> "b":
        return True

    @dbus_property(PropertyAccess.READ)
    def CanGoPrevious(self) -> "b":
        return True

    @dbus_property(PropertyAccess.READ)
    def CanPlay(self) -> "b":
        return True

    @dbus_property(PropertyAccess.READ)
    def CanPause(self) -> "b":
        return True

    @dbus_property(PropertyAccess.READ)
    def CanSeek(self) -> "b":
        return True

    @dbus_property(PropertyAccess.READ)
    def CanControl(self) -> "b":
        return True


class TracklistInterface(ServiceInterface):
    def __init__(self, app):
        name = "org.mpris.MediaPlayer2.TrackList"
        super().__init__(name)
        self._app = app

    @method()
    def GetTracksMetadata(self, tracksid: "ao") -> "aa{sv}":
        return [{"mpris:trackid": Variant("o", id)} for id in tracksid]

    @method()
    def AddTrack(self, uri: "s", after_track: "o", set_as_current: "b"):
        pass

    @method()
    def RemoveTrack(self, trackid: "o"):
        pass

    @method()
    def GoTo(self, trackid: "o"):
        pass

    @dbus_property(access=PropertyAccess.READ)
    def Tracks(self) -> "ao":
        return []

    @dbus_property(access=PropertyAccess.READ)
    def CanEditTracks(self) -> "b":
        return False


class PlaylistsInterface(ServiceInterface):
    def __init__(self, app):
        name = "org.mpris.MediaPlayer2.Playlists"
        super().__init__(name)
        self._app = app

    @method()
    def ActivatePlaylist(self, playlist_id: "o"):
        pass

    @method()
    def GetPlaylists(
        self, index: "u", max_count: "u", order: "s", reverse_order: "b"
    ) -> "a(oss)":
        return []

    @dbus_property(access=PropertyAccess.READ)
    def PlaylistCount(self) -> "u":
        return 0

    @dbus_property(access=PropertyAccess.READ)
    def Orderings(self) -> "as":
        return ["default"]

    @dbus_property(access=PropertyAccess.READ)
    def ActivePlaylist(self) -> "(b(oss))":
        return [False, ["/", "", ""]]


class EventHandler:
    def __init__(self, root, player, tracklist, playlists):
        # getting all the interfaces
        self.root = root
        self.player = player
        self.tracklist = tracklist
        self.playlists = playlists
        self._app = self.player._app

    def on_app_event(self, event):
        # events = ["prev", "next"]
        if event in [Event.PAUSE, Event.PLAY, Event.STOP]:
            self.on_playpause()
        elif event == Event.VOLUME:
            self.on_volume()
        elif event == Event.SHUFFLE:
            self.on_shuffle()
        elif event == Event.REPEAT:
            self.on_loop()
        elif event in [Event.PREV, Event.NEXT]:
            self.on_change_track()

    def on_volume(self):
        self.player.emit_properties_changed({"Volume": self._app.volume})

    def on_playpause(self):
        self.player.emit_properties_changed(
            {"PlaybackStatus": self.player.PlaybackStatus}
        )

    def on_loop(self):
        self.player.emit_properties_changed({"LoopStatus": self.player.LoopStatus})

    def on_shuffle(self):
        self.player.emit_properties_changed({"Shuffle": self.player.Shuffle})

    def on_change_track(self):
        self.player.emit_properties_changed({"Metadata": self.player.Metadata})


async def init(app):
    bus = await MessageBus().connect()
    root = RootInterface(app)
    player = PlayerInterface(app)
    tracklist = TracklistInterface(app)
    playlist = PlaylistsInterface(app)
    app.event_handler = EventHandler(root, player, tracklist, playlist)

    bus.export("/org/mpris/MediaPlayer2", root)
    bus.export("/org/mpris/MediaPlayer2", player)
    bus.export("/org/mpris/MediaPlayer2", tracklist)
    bus.export("/org/mpris/MediaPlayer2", playlist)
    log.info("All interfaces exported")
    await bus.request_name(f"org.mpris.MediaPlayer2.{APP_NAME}")
