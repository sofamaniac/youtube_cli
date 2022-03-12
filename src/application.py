import youtube
import gui.screen as screen
import player
from panel import Panel

from gui.screen import Directions, CurseString
import gui.textbox as textbox

import time

import parser.primitives as primitives

class Application:
    def __init__(self, stdscr):
        self.scr = screen.Screen(stdscr)

        self.contentPanel = Panel(self.scr.contentWin, "Videos")

        self.playlistPanel = Panel(self.scr.playlistsWin, "Playlists")
        self.playlistPanel.source = youtube.PlaylistList()
        self.getPlaylist()

        self.playerPanel = Panel(self.scr.playerWin, "Player Information")
        self.playerPanel.selected = -1

        self.optionPanel = Panel(self.scr.optionWin, "Options")
        self.optionPanel.selected = -1

        self.informationPanel = Panel(self.scr.informationWin, "Informations")

        self.panelsList = [self.playlistPanel, self.contentPanel]
        self.currentPanel = 0

        self.searchPanel = Panel(self.scr.searchWin, "Search")
        self.inSearch = False
        self.textbox = textbox.Textbox(self.scr.searchField)
        self.commandField = textbox.Textbox(self.scr.commandField)

        self.addToPlaylistPanel = Panel(self.scr.addPlaylistWin, "Add to playlist")
        self.addToPlaylistPanel.source = self.playlistPanel.source
        self.addToPlaylistPanel.toggleVisible()  # make window invisible
        self.inAddToPlaylist = False

        self._videoMode = False  # should the video be played alongside the audio
        self.createPlayer()
        self.playing = youtube.Video() 

        self.inPlaylist = False
        self.playlist = youtube.ListItems()
        self.playlistIndex = 0
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
    def videoMode(self):
        return self._videoMode

    @videoMode.setter
    def videoMode(self, val):
        self._videoMode = val
        self.stop()
        self.createPlayer()

    def skipSegment(self):
        time = self.player.time
        time = time if time else 0
        check = self.playing.checkSkip(time)
        duration = self.player.duration
        if check and duration:
            jump = min(check, duration)
            self.player.seek(jump)

    def search(self):
        self.inSearch = True
        self.searchPanel.update()
        self.textbox.reset()
        self.textbox.edit(update=self.update)
        search_term = self.textbox.gather()
        if search_term:
            self.searchPanel.content = [CurseString(search_term)]
            self.contentPanel.source = youtube.Search(search_term)
            self.currentPanel = 1
        self.searchPanel.clear()
        self.inSearch = False
        self.update()

    def command(self):
        self.commandField.reset()
        self.commandField.edit(update=self.update)
        command = self.commandField.gather()
        if command:
            primitives.evaluate(command)

    def update(self):

        # checking if player is still alive
        try:
            self.player.check_alive()
        except player.PlayerDeadError:
            # if not we create a new player
            self.createPlayer()

        # checking for segments to skip
        self.skipSegment()

        # Drawing all the windows
        self.playlistPanel.update()
        self.contentPanel.update()
        self.drawPlayer()
        self.drawOptions()
        self.drawInfo()
        self.drawAddToPlaylist()

        # checking if there is something playing
        if self.inPlaylist and self.player.is_song_finished():  # the current song has finished
            self.next()

        if self.inSearch:
            self.searchPanel.update()

        self.scr.update()


    def drawInfo(self):
        currSelection = self.contentPanel.getSelected()
        content = []
        content.append(CurseString(f"Title: {currSelection.title}"))
        content.append(CurseString(f"Author: {currSelection.author}"))
        content.append(CurseString(f"Id: {currSelection.id}"))
        self.informationPanel.update(drawSelect=False, to_display=content)

    def drawOptions(self):
        content = []

        content.append(CurseString(f"Auto: {self.inPlaylist}"))
        content.append(CurseString(f"Repeat: {self.repeat}"))
        content.append(CurseString(f"Shuffle: {self.shuffled}"))
        content.append(CurseString(f"Volume : {self.volume:02d} / 100"))
        content.append(CurseString(f"Mode: {'Video' if self.videoMode else 'Audio'}"))
        self.optionPanel.update(drawSelect=False, to_display=content)

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
        for i,_ in enumerate(bar):
            if self.playing.checkSkip(i*dur/width):
                s.color(screen.COLOR_SEG, i, i+1)
        content.append(s)

        self.playerPanel.update(drawSelect=False, to_display=content)

    def drawAddToPlaylist(self):

        if not self.addToPlaylistPanel.visible:
            return

        currSelection = self.contentPanel.getSelected()
        content = []

        for p in self.playlistPanel.source.elements:
            if currSelection in p:
                checkbox = "[x]"
            else:
                checkbox = "[ ]"
            content.append(CurseString(f"{checkbox} {p.title}"))

        self.addToPlaylistPanel.update(to_display=content)

    def select(self, direction):
        doUpdate = False
        if direction == Directions.Up or direction == Directions.Down:
            doUpdate = True
            self.getCurrentPanel().select(direction)
        elif direction == Directions.Left and self.currentPanel > 0:
            doUpdate = True
            self.currentPanel -= 1
        elif direction == Directions.Right and self.currentPanel < len(self.panelsList)-1:
            doUpdate = True
            self.currentPanel += 1

        if ( doUpdate and direction in [Directions.Left, Directions.Right] and 
                self.getCurrentPanel() == self.contentPanel
            ):
            self.getPlaylist()
            self.contentPanel.selected = 0

    def setPlaylist(self):
        if not self.inPlaylist:
            self.playlist = self.playlistPanel.getSelected()
            self.shuffled = False
            self.playlist.currentIndex = self.contentPanel.selected
            self.player.stop()
            self.play(self.playlist.getCurrent())
        self.inPlaylist = not self.inPlaylist

    def getPlaylist(self):
        self.contentPanel.source = self.playlistPanel.getSelected()

    def addToPlaylist(self):
        self.inAddToPlaylist = True
        self.addToPlaylistPanel.toggleVisible()

    def editPlaylist(self):
        currSelection = self.contentPanel.getSelected()
        currPlaylist = self.addToPlaylistPanel.getSelected()
        if currSelection in currPlaylist:
            currPlaylist.remove(currSelection)
        else:
            currPlaylist.add(currSelection)
        self.inAddToPlaylist = False
        self.addToPlaylistPanel.toggleVisible()

    def getCurrentPanel(self):
        if self.inAddToPlaylist:
            return self.addToPlaylistPanel
        else:
            return self.panelsList[self.currentPanel]

    def enter(self):
        if self.getCurrentPanel() == self.playlistPanel:
            self.getPlaylist()
            self.currentPanel = 1
        elif self.getCurrentPanel() == self.addToPlaylistPanel:
            self.editPlaylist()
        else:
            if self.inPlaylist:
                self.playlist.setEffectiveIndex(self.contentPanel.selected)
            self.play()

    def escape(self):
        if self.getCurrentPanel() == self.addToPlaylistPanel:
            self.inAddToPlaylist = False
            self.addToPlaylistPanel.toggleVisible()

    def reload(self):
        self.contentPanel.source.reload()

    def next(self):
        if self.inPlaylist:
            if self.playlist.currentIndex > self.playlist.size:
                self.player.stop()
            else:
                self.play(self.playlist.next())
        else:
            panel = self.contentPanel
            panel.select(Directions.Down)
            self.play()

    def prev(self):
        if self.inPlaylist:
            if self.playlist.currentIndex > 0:
                self.play(self.playlist.prev())
            else:
                self.player.stop()
        else:
            panel = self.contentPanel
            panel.select(Directions.Up)
            self.play()

    def nextPage(self):
        self.getCurrentPanel().next_page()

    def prevPage(self):
        self.getCurrentPanel().prev_page()

    def play(self, to_play=youtube.Video()):
        selected = self.contentPanel.getSelected()
        if not to_play.id and selected.id != self.playing.id:
            to_play = selected
        url = to_play.getUrl(self.videoMode)
        self.player.play(url)
        self.playing = to_play
        # when nothing is playing, the volume might not get updated on the backend
        # therefore we update it manually each time something is played
        # TODO not working
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

    def createPlayer(self):
        if self.videoMode:
            self.player = player.VideoPlayer()
        else:
            self.player = player.AudioPlayer()

    def toggleVideo(self):
        self.videoMode = not self.videoMode

    def toggleShuffle(self):
        self.shuffled = not self.shuffled

    def quit(self):
        self.stop()
        self.player.quit()
        return
