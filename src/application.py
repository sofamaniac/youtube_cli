import youtube
import gui.screen as screen
import player
from panel import Panel

from gui.screen import Directions, CurseString
from gui import textbox

import time

from parser import primitives

from folder import FolderList
from playlist import PlaylistList


class Application:
    def __init__(self, stdscr):
        self.scr = screen.Screen(stdscr)

        self.content_panel = Panel(self.scr.content_win, "Videos")

        self.playlist_panel = Panel(self.scr.playlists_win, "Playlists")
        self.playlist_panel.source = PlaylistList()
        youtubePlaylists = youtube.PlaylistList()
        for p in youtubePlaylists.elements:
            self.playlist_panel.source.add_playlist(p)
        folders = FolderList()
        for f in folders.elements:
            self.playlist_panel.source.add_playlist(f)
        self.getPlaylist()

        self.player_panel = Panel(self.scr.player_win, "Player Information")
        self.player_panel.selected = -1

        self.option_panel = Panel(self.scr.option_win, "Options")
        self.option_panel.selected = -1

        self.information_panel = Panel(self.scr.information_win, "Informations")

        self.panels_list = [self.playlist_panel, self.content_panel]
        self.current_panel = 0

        self.search_panel = Panel(self.scr.search_win, "Search")
        self.in_search = False
        self.textbox = textbox.Textbox(self.scr.search_field)
        self.command_field = textbox.Textbox(self.scr.command_field)

        self.add_to_playlist_panel = Panel(self.scr.add_playlist_win, "Add to playlist")
        self.add_to_playlist_panel.source = self.playlist_panel.source
        self.add_to_playlist_panel.toggle_visible()  # make window invisible
        self.in_add_to_playlist = False

        self._video_mode = False  # should the video be played alongside the audio
        self.create_player()
        self.playing = youtube.Video()

        self.in_playlist = False
        self.playlist = youtube.YoutubeList()
        self.playlist_index = 0
        self.repeat = "No"
        self.shuffled = False

        self.volume = 50
        self.muted = False

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, vol):
        if not 0 <= vol <= 100:
            return
        self._volume = vol
        self.player.set_volume(self.volume)

    @property
    def repeat(self):
        return self._repeat

    @repeat.setter
    def repeat(self, value):
        self._repeat = value
        self.player.set_repeat(self.repeat)

    @property
    def muted(self):
        return self._muted

    @muted.setter
    def muted(self, value):
        self._muted = value
        if self.muted:
            self.player.set_volume(0)
        else:
            self.player.set_volume(self.volume)

    @property
    def shuffled(self):
        return self._shuffled

    @shuffled.setter
    def shuffled(self, val):
        self._shuffled = val
        if self._shuffled:
            self.playlist.shuffle()
        else:
            self.playlist.unshuffle()

    @property
    def video_mode(self):
        return self._video_mode

    @video_mode.setter
    def video_mode(self, val):
        self._video_mode = val
        self.stop()
        self.create_player()

    def skipSegment(self):
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
            self.current_panel = 1
        self.search_panel.clear()
        self.in_search = False
        self.update()

    def command(self):
        self.command_field.reset()
        self.command_field.edit(update=self.update)
        command = self.command_field.gather()
        if command:
            primitives.evaluate(command)

    def update(self):

        # checking if player is still alive
        try:
            self.player.check_alive()
        except player.PlayerDeadError:
            # if not we create a new player
            self.create_player()

        # checking for segments to skip
        self.skipSegment()

        # Drawing all the windows
        self.playlist_panel.update()
        self.content_panel.update()
        self.drawPlayer()
        self.drawOptions()
        self.drawInfo()
        self.drawAddToPlaylist()

        # checking if there is something playing
        if (
            self.in_playlist and self.player.is_song_finished()
        ):  # the current song has finished
            self.next()

        if self.in_search:
            self.search_panel.update()

        self.scr.update()

    def drawInfo(self):
        selection = self.content_panel.get_selected()
        content = []
        content.append(CurseString(f"Title: {selection.title}"))
        content.append(CurseString(f"Author: {selection.author}"))
        content.append(CurseString(f"Id: {selection.id}"))
        self.information_panel.update(draw_select=False, to_display=content)

    def drawOptions(self):
        content = []

        content.append(CurseString(f"Auto: {self.in_playlist}"))
        content.append(CurseString(f"Repeat: {self.repeat}"))
        content.append(CurseString(f"Shuffle: {self.shuffled}"))
        content.append(CurseString(f"Volume : {self.volume:02d} / 100"))
        content.append(CurseString(f"Mode: {'Video' if self.video_mode else 'Audio'}"))
        self.option_panel.update(draw_select=False, to_display=content)

    def drawPlayer(self):
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
        width = screen.PLAYER_WIDTH - 5 - len(" {}/{}".format(t, d))
        whole = "\u2588" * int(frac_time * width)
        space = "\u2500" * (width - len(whole))
        bar = whole + space
        progress = "\u2595" + bar + "\u258F" + " {}/{}".format(t, d)
        s = CurseString(progress)
        for i, _ in enumerate(bar):
            if self.playing.check_skip(i * dur / width):
                s.color(screen.COLOR_SEG, i, i + 1)
        content.append(s)

        self.player_panel.update(draw_select=False, to_display=content)

    def drawAddToPlaylist(self):

        if not self.add_to_playlist_panel.visible:
            return

        currSelection = self.content_panel.get_selected()
        content = []

        for p in self.playlist_panel.source.elements:
            if currSelection in p:
                checkbox = "[x]"
            else:
                checkbox = "[ ]"
            content.append(CurseString(f"{checkbox} {p.title}"))

        self.add_to_playlist_panel.update(to_display=content)

    def select(self, direction):
        doUpdate = False
        if direction == Directions.UP or direction == Directions.DOWN:
            doUpdate = True
            self.getCurrentPanel().select(direction)
        elif direction == Directions.LEFT and self.current_panel > 0:
            doUpdate = True
            self.current_panel -= 1
        elif (
            direction == Directions.RIGHT
            and self.current_panel < len(self.panels_list) - 1
        ):
            doUpdate = True
            self.current_panel += 1

        if (
            doUpdate
            and direction in [Directions.LEFT, Directions.RIGHT]
            and self.getCurrentPanel() == self.content_panel
        ):
            self.getPlaylist()
            self.content_panel.selected = 0

    def setPlaylist(self):
        if not self.in_playlist:
            self.playlist = self.playlist_panel.get_selected()
            self.shuffled = self.shuffled  # force update
            self.playlist.currentIndex = self.content_panel.selected
            self.player.stop()
            self.play(self.playlist.get_current())
        self.in_playlist = not self.in_playlist

    def getPlaylist(self):
        self.content_panel.source = self.playlist_panel.get_selected()

    def addToPlaylist(self):
        self.in_add_to_playlist = True
        self.add_to_playlist_panel.toggle_visible()

    def editPlaylist(self):
        currSelection = self.content_panel.get_selected()
        currPlaylist = self.add_to_playlist_panel.get_selected()
        if currSelection in currPlaylist:
            currPlaylist.remove(currSelection)
        else:
            currPlaylist.add(currSelection)
        self.in_add_to_playlist = False
        self.add_to_playlist_panel.toggle_visible()

    def getCurrentPanel(self):
        if self.in_add_to_playlist:
            return self.add_to_playlist_panel
        else:
            return self.panels_list[self.current_panel]

    def enter(self):
        if self.getCurrentPanel() == self.playlist_panel:
            self.getPlaylist()
            self.current_panel = 1
        elif self.getCurrentPanel() == self.add_to_playlist_panel:
            self.editPlaylist()
        else:
            if self.in_playlist:
                self.playlist.set_effective_index(self.content_panel.selected)
            self.play()

    def escape(self):
        if self.getCurrentPanel() == self.add_to_playlist_panel:
            self.in_add_to_playlist = False
            self.add_to_playlist_panel.toggle_visible()

    def reload(self):
        self.content_panel.source.reload()

    def next(self):
        if self.in_playlist:
            if self.playlist.currentIndex > self.playlist.size:
                self.player.stop()
            else:
                self.play(self.playlist.next())
        else:
            panel = self.content_panel
            panel.select(Directions.DOWN)
            self.play()

    def prev(self):
        if self.in_playlist:
            if self.playlist.currentIndex > 0:
                self.play(self.playlist.prev())
            else:
                self.player.stop()
        else:
            panel = self.content_panel
            panel.select(Directions.UP)
            self.play()

    def nextPage(self):
        self.getCurrentPanel().next_page()

    def prevPage(self):
        self.getCurrentPanel().prev_page()

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
        self.increaseVolume(0)

    def stop(self):
        self.player.stop()
        self.playing = youtube.Video()

    def pause(self):
        self.player.pause()

    def toggleRepeat(self):
        values = ["No", "Song", "Playlist"]
        self.repeat = values[values.index(self.repeat)]
        self.player.set_repeat(self.repeat)

    def forward(self, dt):
        if not self.player.is_playing():
            return
        self.player.seek(dt)

    def seekPercent(self, percent):
        if not self.player.is_playing():
            return
        self.player.seek_percent(percent)

    def increaseVolume(self, dv):
        self.volume += dv

    def toggleMute(self):
        self.muted = not self.muted

    def create_player(self):
        if self.video_mode:
            self.player = player.VideoPlayer()
        else:
            self.player = player.AudioPlayer()

    def toggleVideo(self):
        self.video_mode = not self.video_mode

    def toggleShuffle(self):
        self.shuffled = not self.shuffled

    def quit(self):
        self.stop()
        self.player.quit()
        return
