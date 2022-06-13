"""Main component of the program, where most of the logic is handled"""

import youtube
import gui.screen as screen
import player
from widget import Widget, PlaylistPanel

from gui.screen import Directions, CurseString, PanelDirections
from gui import textbox
from gui import panel

import time
import logging

log = logging.getLogger(__name__)

from folder import FolderList
from playlist import PlaylistList

from property import Property


class Application:
    """The core of the application"""

    def __init__(self, stdscr):
        self.property_list = []
        self.scr = screen.Screen(stdscr)

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

        self.player_panel = Widget(
            "Player Information",
            0,
            0,
            100,
            4,
            h_mode=panel.ABSOLUTE_MODE,
            screen=self.scr,
        )
        self.player_panel.set_below_of(self.content_panel)
        self.player_panel.selectable = False

        self.option_panel = Widget("Options", 0, 0, 20, 20, screen=self.scr)
        self.option_panel.set_below_of(self.local_playlist_panel)
        self.option_panel.selectable = False

        self.information_panel = Widget("Informations", 0, 0, 20, 15, screen=self.scr)
        self.information_panel.set_below_of(self.option_panel)
        self.information_panel.selectable = False

        self.yt_playlist_panel.source = PlaylistList()
        self.local_playlist_panel.source = PlaylistList()
        youtubePlaylists = youtube.YoutubePlaylistList()
        for p in youtubePlaylists.elements:
            self.yt_playlist_panel.source.add_playlist(p)
        folders = FolderList()
        for f in folders.elements:
            self.local_playlist_panel.source.add_playlist(f)
        self.current_panel = self.yt_playlist_panel
        self.get_playlist()

        self.search_panel = Widget("Search", 0, 0, 80, 12, screen=self.scr)
        self.in_search = False
        self.textbox = textbox.Textbox(0, 0, 80, 12, screen=self.scr)
        self.command_field = textbox.Textbox(0, 10, 1000, 12, screen=self.scr)

        self.add_to_playlist_panel = Widget(
            "Add to playlist", 0, 0, 20, 20, screen=self.scr
        )
        self.add_to_playlist_panel.source = self.yt_playlist_panel.source
        self.add_to_playlist_panel.toggle_visible()  # make window invisible
        self.add_to_playlist_panel.center()
        self.in_add_to_playlist = False

        # should the video be played alongside the audio
        self.__add_property("video_mode", False)
        self.create_player()
        self.playing = youtube.Video()

        self.__add_property("in_playlist", False)
        self.playlist = youtube.YoutubeList()
        self.playlist_index = 0
        self.__add_property("repeat", "No")
        self.__add_property("shuffled", False)

        self.__add_property("volume", 50)
        self.__add_property("muted", False)

    def __add_property(self, name, value=None):
        self.__dict__[name] = Property(name, value)
        self.property_list.append(name)

    def __set_property(self, name, value):
        if name in self.property_list:
            self.__dict__[name].set(value)

    def __getattribute__(self, name):
        if name == "property_list" or not name in self.property_list:
            return super(Application, self).__getattribute__(name)
        else:
            return self.__dict__[name].get()

    def __setattr__(self, name, value):
        match name:
            case "volume":
                if not 0 <= value <= 100:
                    return
                self.__set_property(name, value)
                self.player.set_volume(self.volume)
            case "in_playlist":
                self.__set_property(name, value)
            case "repeat":
                self.__set_property(name, value)
                self.player.set_repeat(self.repeat)
            case "muted":
                self.__set_property(name, value)
                if self.muted:
                    self.player.set_volume(0)
                else:
                    self.player.set_volume(self.volume)
            case "shuffled":
                self.__set_property(name, value)
                if self.shuffled:
                    self.playlist.shuffle()
                else:
                    self.playlist.unshuffle()
            case "video_mode":
                self.__set_property(name, value)
                self.stop()
                self.create_player()
            case _:
                super(Application, self).__setattr__(name, value)

    def skip_segment(self):
        time = self.player.time
        time = time if time else 0
        check = self.playing.check_skip(time)
        duration = self.player.duration
        if check and duration:
            jump = min(check, duration)
            self.player.seek(jump)

    def search(self):
        self.in_search = True
        self.search_panel.update()
        self.textbox.reset()
        self.textbox.edit(update=self.update)
        search_term = self.textbox.gather()
        if search_term:
            self.search_panel.content = [CurseString(search_term)]
            self.content_panel.source = youtube.Search(search_term)
            self.current_panel = self.content_panel
        self.search_panel.clear()
        self.in_search = False
        self.update()

    def command(self):
        self.command_field.reset()
        self.command_field.edit(update=self.update)
        command = self.command_field.gather()
        if command:
            # TODO
            log.info("command passed")
            pass

    def update(self):

        # checking if player is still alive
        try:
            self.player.check_alive()
        except player.PlayerDeadError:
            # if not we create a new player
            self.create_player()

        # checking for segments to skip
        self.skip_segment()

        # Drawing all the windows
        self.yt_playlist_panel.update(
            draw_select=self.current_panel == self.yt_playlist_panel
        )
        self.local_playlist_panel.update(
            draw_select=self.current_panel == self.local_playlist_panel
        )
        self.content_panel.update(draw_select=self.current_panel == self.content_panel)
        self.draw_player()
        self.draw_options()
        self.draw_info()

        # checking if there is something playing
        if (
            self.in_playlist and self.player.is_song_finished()
        ):  # the current song has finished
            self.next()

        if self.in_search:
            self.search_panel.update()

        self.draw_add_to_playlist()

        self.scr.update()

    def draw_info(self):
        selection = self.content_panel.get_selected()
        content = []
        content.append(CurseString(f"Title: {selection.title}"))
        content.append(CurseString(f"Author: {selection.author}"))
        content.append(CurseString(f"Id: {selection.id}"))
        self.information_panel.update(to_display=content)

    def draw_options(self):
        content = []

        content.append(CurseString(f"Auto: {self.in_playlist}"))
        content.append(CurseString(f"Repeat: {self.repeat}"))
        content.append(CurseString(f"Shuffle: {self.shuffled}"))
        content.append(CurseString(f"Volume : {self.volume:02d} / 100"))
        content.append(CurseString(f"Mode: {'Video' if self.video_mode else 'Audio'}"))
        self.option_panel.update(to_display=content)

    def draw_player(self):
        title = self.playing.title
        dur = self.player.duration

        time_pos = self.player.time

        t = time.strftime("%H:%M:%S", time.gmtime(time_pos))
        d = time.strftime("%H:%M:%S", time.gmtime(dur))

        t = t if time_pos else "00:00:00"
        d = d if dur else "00:00:00"
        content = [CurseString(f"{title} - {t}/{d}")]

        # drawing progress bar
        time_pos = time_pos if time_pos else 0
        dur = dur if dur else 0
        frac_time = time_pos / (dur + 1)
        width = self.player_panel.width - 5 - len(" {}/{}".format(t, d))
        whole = "\u2588" * int(frac_time * width)
        space = "\u2500" * (width - len(whole))
        bar = whole + space
        progress = "\u2595" + bar + "\u258F" + " {}/{}".format(t, d)
        s = CurseString(progress)
        for i, _ in enumerate(bar):
            if self.playing.check_skip(i * dur / width):
                s.color(screen.COLOR_SEG, i, i + 1)
        content.append(s)

        self.player_panel.update(to_display=content)

    def draw_add_to_playlist(self):

        if not self.in_add_to_playlist:
            return

        currSelection = self.content_panel.get_selected()
        content = []

        for p in self.yt_playlist_panel.source.elements:
            if currSelection in p:
                checkbox = "[x]"
            else:
                checkbox = "[ ]"
            content.append(CurseString(f"{checkbox} {p.title}"))

        self.add_to_playlist_panel.update(to_display=content)

    def select(self, direction):
        do_update = False
        reset_pos = False
        if isinstance(direction, Directions):
            do_update = True
            self.current_panel.select(direction)
        elif isinstance(direction, PanelDirections):
            tmp = self.current_panel.get_next_selectable_neighbour(direction)
            if tmp:
                do_update = True
                self.current_panel = tmp
            reset_pos = tmp == self.content_panel

        if do_update and reset_pos and self.current_panel == self.content_panel:
            self.get_playlist()
            self.content_panel.selected = 0

    def set_playlist(self):
        if not self.in_playlist:
            if isinstance(self.current_panel, PlaylistPanel):
                self.playlist = self.current_panel.get_selected()
            else:
                self.playlist = self.content_panel.source
            self.shuffled = self.shuffled  # force update
            self.playlist.current_index = self.content_panel.selected
            self.player.stop()
            self.in_playlist = True
            self.play(self.playlist.get_current())
        else:
            self.in_playlist = False

    def get_playlist(self):
        if isinstance(self.current_panel, PlaylistPanel):
            self.content_panel.source = self.current_panel.get_selected()

    def add_to_playlist(self):
        self.in_add_to_playlist = True
        self.add_to_playlist_panel.toggle_visible()
        self.current_panel = self.add_to_playlist_panel

    def edit_playlist(self):
        currSelection = self.content_panel.get_selected()
        currPlaylist = self.add_to_playlist_panel.get_selected()
        if currSelection in currPlaylist:
            currPlaylist.remove(currSelection)
        else:
            currPlaylist.add(currSelection)
        self.in_add_to_playlist = False
        self.add_to_playlist_panel.toggle_visible()
        self.current_panel = self.content_panel

    def enter(self):
        if isinstance(self.current_panel, PlaylistPanel):
            self.get_playlist()
            self.current_panel = self.content_panel
        elif self.current_panel == self.add_to_playlist_panel:
            self.edit_playlist()
        else:
            if self.in_playlist:
                self.playlist.set_effective_index(self.content_panel.selected)
            self.play()

    def escape(self):
        if self.in_add_to_playlist:
            self.in_add_to_playlist = False
            self.add_to_playlist_panel.toggle_visible()
            self.current_panel = self.content_panel

    def reload(self):
        self.content_panel.source.reload()

    def next(self):
        if self.in_playlist:
            if self.playlist.current_index > self.playlist.size:
                self.player.stop()
            else:
                self.play(self.playlist.next())
            self.playlist.get_next().fetch_url()
        else:
            panel = self.content_panel
            panel.select(Directions.DOWN)
            self.play()

    def prev(self):

        # if the song was started less than 10 seconds ago
        if self.player.time < 10:
            if self.in_playlist:
                if self.playlist.current_index > 0:
                    self.play(self.playlist.prev())
                else:
                    self.player.stop()
            else:
                panel = self.content_panel
                panel.select(Directions.UP)
                self.play()

        # else we start the same song
        else:
            self.player.seek_percent(0)

    def next_page(self):
        self.current_panel.next_page()

    def prev_page(self):
        self.current_panel.prev_page()

    def play(self, to_play=youtube.Video()):
        selected = self.content_panel.get_selected()
        if not to_play.id and selected.id != self.playing.id:
            to_play = selected
        url = to_play.get_url(self.video_mode)
        self.player.play(url)
        self.playing = to_play
        # when nothing is playing, the volume might not get updated on the backend
        # therefore we update it manually each time something is played
        # TODO not working or maybe it is
        self.increase_volume(0)

    def stop(self):
        self.player.stop()
        self.playing = youtube.Video()

    def pause(self):
        self.player.pause()

    def toggle_repeat(self):
        values = ["No", "Song", "Playlist"]
        self.repeat = values[(values.index(self.repeat) + 1) % len(values)]
        self.player.set_repeat(self.repeat)

    def forward(self, dt):
        if not self.player.is_playing():
            return
        self.player.seek(dt)

    def seek_percent(self, percent):
        if not self.player.is_playing():
            return
        self.player.seek_percent(percent)

    def increase_volume(self, dv):
        self.volume += dv

    def toggle_mute(self):
        self.muted = not self.muted

    def create_player(self):
        if self.video_mode:
            self.player = player.VideoPlayer()
        else:
            self.player = player.AudioPlayer()

    def toggle_video(self):
        self.video_mode = not self.video_mode

    def toggle_shuffle(self):
        self.shuffled = not self.shuffled

    def quit(self):
        self.stop()
        self.player.quit()
        return

    def resize(self):
        self.scr.resize()
        self.yt_playlist_panel.resize()
        self.content_panel.resize()
        self.player_panel.resize()
        self.information_panel.resize()
        self.option_panel.resize()

    def jump_to_current_playing(self):
        self.current_panel = self.content_panel
        self.current_panel.jump_to_selection()
        self.update()
