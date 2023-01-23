"""Main component of the program, where most of the logic is handled"""

import asyncio
import time
import logging

import youtube
import player

from widget import Widget, PlaylistPanel
from gui import screen, textbox, panel
from gui.screen import Directions, CurseString, PanelDirections

from folder import FolderList
from playlist import PlaylistList, Playable

from property import (
    Property,
    PropertyObject,
    global_properties,
    NoneType,
    PropertyDoNotApplyChange,
)

from confLang import parser

from enum import Enum, auto


class PlayerStates(Enum):
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()


class RepeatStates(Enum):
    DISABLED = auto()
    SONG = auto()
    PLAYLIST = auto()


log = logging.getLogger(__name__)


def get_property(name):
    return global_properties.find_property(name).get()


class InfoPanel(Widget):
    def __init__(self, *args, **kwargs):

        super().__init__("Information", *args, **kwargs)
        self.selectable = False

    async def update(self, draw_select=False):

        selection = await get_property("application").content_panel.get_selected()
        if selection is None:
            return
        content = []
        content.append(CurseString(f"Title: {selection.title}"))
        content.append(CurseString(f"Author: {selection.author}"))
        content.append(CurseString(f"Id: {selection.id}"))
        await super().update(to_display=content)


class OptionPanel(Widget):
    def __init__(self, *args, **kwargs):

        super().__init__("Options", *args, **kwargs)
        self.selectable = False

    async def update(self, draw_select=False):

        content = []
        content.append(CurseString(f"Auto: {get_property('in_playlist')}"))
        content.append(CurseString(f"Repeat: {get_property('repeat')}"))
        content.append(CurseString(f"Shuffle: {get_property('shuffled')}"))
        content.append(CurseString(f"Volume : {get_property('volume'):02d} / 100"))
        content.append(
            CurseString(f"Mode: {'Video' if get_property('video_mode') else 'Audio'}")
        )
        await super().update(to_display=content)


class PlayerPanel(Widget):
    def __init__(self, *args, **kwargs):

        super().__init__("Player Information", *args, **kwargs)
        self.selectable = False

    async def update(self, draw_select=False):

        playing = get_property("playing")
        player = get_property("player")
        title = playing.title
        dur = player.duration

        time_pos = player.time

        t = time.strftime("%H:%M:%S", time.gmtime(time_pos))
        d = time.strftime("%H:%M:%S", time.gmtime(dur))

        t = t if time_pos else "00:00:00"
        d = d if dur else "00:00:00"
        content = [CurseString(f"{title} - {t}/{d}")]

        # drawing progress bar
        time_pos = time_pos if time_pos else 0
        dur = dur if dur else 0
        frac_time = time_pos / (dur + 1)
        width = self.width - 5 - len(" {}/{}".format(t, d))
        whole = "\u2588" * int(frac_time * width)
        space = "\u2500" * (width - len(whole))
        bar_string = whole + space
        progress = "\u2595" + bar_string + "\u258F" + " {}/{}".format(t, d)
        s = CurseString(progress)
        for i, _ in enumerate(bar_string):
            if await playing.check_skip(i * dur / width):
                s.color(screen.COLOR_SEG, i, i + 1)
        content.append(s)

        await super().update(to_display=content)


class Application(PropertyObject):
    """The core of the application"""

    def __init__(self, stdscr):
        super().__init__()
        self.scr = screen.Screen(stdscr)
        self.event_handler = None

        self.yt_playlist_panel = PlaylistPanel(
            "Youtube Playlists", 0, 0, 20, 20, screen=self.scr
        )
        self.local_playlist_panel = PlaylistPanel(
            "Local Playlists", 0, 0, 20, 20, screen=self.scr
        )
        self.local_playlist_panel.set_below_of(self.yt_playlist_panel)
        self.content_panel = Widget("Videos", 0, 0, 80, 88, screen=self.scr)
        self.content_panel.set_right_to(self.yt_playlist_panel)
        self.content_panel.set_right_to(self.local_playlist_panel)

        self.player_panel = PlayerPanel(
            0,
            0,
            100,
            4,
            h_mode=panel.ABSOLUTE_MODE,
            screen=self.scr,
        )
        self.player_panel.set_below_of(self.content_panel)

        self.option_panel = OptionPanel(0, 0, 20, 20, screen=self.scr)
        self.option_panel.set_below_of(self.local_playlist_panel)

        self.information_panel = InfoPanel(0, 0, 20, 15, screen=self.scr)
        self.information_panel.set_below_of(self.option_panel)

        self.yt_playlist_panel.source = PlaylistList()
        self.local_playlist_panel.source = PlaylistList()
        self.current_panel = self.yt_playlist_panel

        self.search_panel = Widget("Search", 0, 0, 80, 12, screen=self.scr)
        self.in_search = False
        self.textbox = textbox.Textbox(0, 0, 80, 12, screen=self.scr)
        self.command_field = textbox.Textbox(0, 0, 80, 3, screen=self.scr)

        self.add_to_playlist_panel = Widget(
            "Add to playlist", 0, 0, 20, 20, screen=self.scr
        )
        self.add_to_playlist_panel.source = self.yt_playlist_panel.source
        self.add_to_playlist_panel.toggle_visible()  # make window invisible
        self.add_to_playlist_panel.center()
        self.in_add_to_playlist = False

        # should the video be played alongside the audio
        self.video_mode = None  # avoid linting errors
        self._add_property(
            "video_mode", False, post_change_hook=self._change_video_mode
        )
        self.player = None
        self._add_property("player", player.AudioPlayer(), base_type=player.Player)
        self.create_player()
        self.playing = None
        self._add_property("playing", youtube.Video(), base_type=Playable)

        self.in_playlist = None
        self._add_property("in_playlist", False)
        self.playlist = youtube.YoutubeList()
        self.playlist_index = 0
        self.repeat = None
        self._add_property("repeat", "No", pre_change_hook=self._change_repeat)
        self.shuffled = None
        self._add_property("shuffled", False, pre_change_hook=self._change_shuffled)

        self.volume = None
        self._add_property("volume", 50, pre_change_hook=self._change_volume)
        self.muted = None
        self._add_property("muted", False, pre_change_hook=self._change_muted)
        global_properties.add_property(Property("application", self))  # maybe overkill

        self.state = PlayerStates.STOPPED

    async def init(self):
        folders = FolderList()
        await folders.init()
        for f in folders.elements:
            self.local_playlist_panel.source.add_playlist(f)
        youtubePlaylists = youtube.YoutubePlaylistList()
        await youtubePlaylists.init()
        for p in youtubePlaylists.elements:
            self.yt_playlist_panel.source.add_playlist(p)
        await self.get_playlist()

    def _change_volume(self, value):
        if 0 <= value <= 100:
            self.player.set_volume(value)
        else:
            raise PropertyDoNotApplyChange

    def _change_repeat(self, value):
        self.player.set_repeat(value)

    def _change_muted(self, value):
        if value:
            self.player.set_volume(self.volume)
        else:
            self.player.set_volume(0)

    def _change_shuffled(self, value):
        if value:
            asyncio.gather(self.playlist.shuffle())
        else:
            asyncio.gather(self.playlist.unshuffle())

    def _change_video_mode(self):
        timestamp = self.player.time
        asyncio.gather(self.stop())
        self.create_player()
        if self.in_playlist or timestamp:
            asyncio.gather(self.play())
            while not self.player.duration:
                time.sleep(0.1)
            self.player.seek(timestamp, mode="absolute")

    async def skip_segment(self):
        timestamp = self.player.time
        timestamp = timestamp if timestamp else 0
        check = await self.playing.check_skip(timestamp)
        duration = self.player.duration
        if check and duration:
            jump = min(check, duration)
            self.player.seek(jump)

    async def search(self):
        self.in_search = True
        await self.search_panel.update()
        self.textbox.reset()
        self.textbox.edit(update=self.update)
        search_term = self.textbox.gather()
        if search_term:
            self.search_panel.content = [CurseString(search_term)]
            self.content_panel.source = youtube.Search(search_term)
            self.current_panel = self.content_panel
        self.search_panel.clear()
        self.in_search = False
        await self.update()

    async def command(self):
        self.command_field.reset()
        self.command_field.edit(update=self.update)
        command = self.command_field.gather()
        if command:
            # TODO
            parser.evaluate(command)
            log.info("command passed")

    async def update(self):

        # checking if player is still alive
        try:
            self.player.check_alive()
        except player.PlayerDeadError:
            # if not we create a new player
            self.create_player()

        # checking for segments to skip
        await self.skip_segment()

        # Drawing all the windows
        await self.yt_playlist_panel.update(
            draw_select=self.current_panel == self.yt_playlist_panel
        )
        await self.local_playlist_panel.update(
            draw_select=self.current_panel == self.local_playlist_panel
        )
        await self.content_panel.update(
            draw_select=self.current_panel == self.content_panel
        )
        await self.player_panel.update()
        await self.option_panel.update()
        await self.information_panel.update()

        # checking if there is something playing
        if (
            self.in_playlist and self.player.is_song_finished()
        ):  # the current song is finished
            await self.next()

        if self.in_search:
            await self.search_panel.update()

        await self.draw_add_to_playlist()

        self.scr.update()

    async def draw_add_to_playlist(self):

        if not self.in_add_to_playlist:
            return

        currSelection = await self.content_panel.get_selected()
        content = []

        for p in self.yt_playlist_panel.source.elements:
            if currSelection in p:
                checkbox = "[x]"
            else:
                checkbox = "[ ]"
            content.append(CurseString(f"{checkbox} {p.title}"))

        await self.add_to_playlist_panel.update(to_display=content)

    async def select(self, direction):
        do_update = False
        reset_pos = False
        if isinstance(direction, Directions):
            do_update = True
            await self.current_panel.select(direction)
        elif isinstance(direction, PanelDirections):
            tmp = self.current_panel.get_next_selectable_neighbour(direction)
            if tmp:
                do_update = True
                self.current_panel = tmp
            reset_pos = tmp == self.content_panel

        if do_update and reset_pos and self.current_panel == self.content_panel:
            await self.get_playlist()
            self.content_panel.selected = 0

    async def set_playlist(self):
        if not self.in_playlist:
            if isinstance(self.current_panel, PlaylistPanel):
                self.playlist = await self.current_panel.get_selected()
            else:
                self.playlist = self.content_panel.source
            self.shuffled = self.shuffled  # force update
            self.playlist.current_index = self.content_panel.selected
            self.player.stop()
            self.in_playlist = True
            await self.play(await self.playlist.get_current())
        else:
            self.in_playlist = False

    async def get_playlist(self):
        if isinstance(self.current_panel, PlaylistPanel):
            self.content_panel.source = await self.current_panel.get_selected()

    async def add_to_playlist(self):
        self.in_add_to_playlist = True
        self.add_to_playlist_panel.toggle_visible()
        self.current_panel = self.add_to_playlist_panel

    async def edit_playlist(self):
        currSelection = await self.content_panel.get_selected()
        currPlaylist = await self.add_to_playlist_panel.get_selected()
        if currSelection in currPlaylist:
            currPlaylist.remove(currSelection)
        else:
            currPlaylist.add(currSelection)
        self.in_add_to_playlist = False
        self.add_to_playlist_panel.toggle_visible()
        self.current_panel = self.content_panel

    async def enter(self):
        if isinstance(self.current_panel, PlaylistPanel):
            await self.get_playlist()
            self.current_panel = self.content_panel
        elif self.current_panel == self.add_to_playlist_panel:
            await self.edit_playlist()
        else:
            if self.in_playlist:
                await self.playlist.set_effective_index(self.content_panel.selected)
            await self.play()

    async def escape(self):
        if self.in_add_to_playlist:
            self.in_add_to_playlist = False
            self.add_to_playlist_panel.toggle_visible()
            self.current_panel = self.content_panel

    async def reload(self):
        await self.content_panel.source.reload()

    async def next(self):
        if self.in_playlist:
            if self.playlist.current_index > self.playlist.size:
                self.player.stop()
            else:
                new = await self.playlist.next()
                next = await self.playlist.get_next()
                await next.fetch_url()
                await self.play(new)
        else:
            await self.content_panel.select(Directions.DOWN)
            await self.play()
        self.event_handler.on_app_event("next")

    async def prev(self):

        # if the song was started less than 10 seconds ago
        if self.player.time < 10:
            if self.in_playlist:
                if self.playlist.current_index > 0:
                    await self.play(await self.playlist.prev())
                else:
                    self.player.stop()
            else:
                self.content_panel.select(Directions.UP)
                await self.play()

        # else we start the same song
        else:
            self.player.seek_percent(0)
        self.event_handler.on_app_event("prev")

    async def next_page(self):
        await self.current_panel.next_page()

    async def prev_page(self):
        await self.current_panel.prev_page()

    async def play(self, to_play=youtube.Video()):
        selected = await self.content_panel.get_selected()
        if not to_play.id and selected.id != self.playing.id:
            to_play = selected
        url = await to_play.get_url(self.video_mode)
        self.player.play(url)
        self.playing = to_play
        # when nothing is playing, the volume might not get updated on the backend
        # therefore we update it manually each time something is played
        await self.increase_volume(0)
        self.state = PlayerStates.PLAYING
        self.player.pause(False)

    async def start(self):
        if not self.playing.id:  # nothing is playing
            pass
        else:
            await self.play()
        self.event_handler.on_app_event("play")

    async def stop(self):
        self.player.stop()
        self.playing = youtube.Video()
        self.event_handler.on_app_event("stop")

    async def pause(self, b=None):
        self.player.pause(b)
        if self.state == PlayerStates.PLAYING:
            self.state = PlayerStates.PAUSED
        else:
            self.state = PlayerStates.PLAYING
        self.event_handler.on_app_event("pause")

    async def toggle_repeat(self):
        values = ["No", "Song", "Playlist"]
        self.repeat = values[(values.index(self.repeat) + 1) % len(values)]
        self.player.set_repeat(self.repeat)
        self.event_handler.on_app_event("repeat")

    def is_playing(self):
        return self.state == PlayerStates.PLAYING

    async def forward(self, dt):
        if not self.player.is_playing():
            return
        self.player.seek(dt)

    async def seek_percent(self, percent):
        if not self.player.is_playing():
            return
        self.player.seek_percent(percent)

    async def increase_volume(self, dv):
        self.volume += dv
        self.event_handler.on_app_event("volume")

    async def toggle_mute(self):
        self.muted = not self.muted

    def create_player(self, video=False):
        if self.video_mode:
            self.player = player.VideoPlayer()
        else:
            self.player = player.AudioPlayer()

    async def toggle_video(self):
        self.video_mode = not self.video_mode

    async def toggle_shuffle(self):
        self.shuffled = not self.shuffled
        self.event_handler.on_app_event("shuffle")

    def quit(self):
        self.stop()
        self.player.quit()

    def resize(self):
        self.scr.resize()
        self.yt_playlist_panel.resize()
        self.content_panel.resize()
        self.player_panel.resize()
        self.information_panel.resize()
        self.option_panel.resize()

    async def jump_to_current_playing(self):
        self.current_panel = self.content_panel
        await self.current_panel.jump_to_selection()
        await self.update()
