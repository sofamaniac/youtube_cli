import youtube
import gui.screen as screen
import player

from gui.screen import Directions, CurseString
import curses
import gui.textbox as textbox

import time

class Window:
    def __init__(self, win, title):
        self.source = None
        self.selected = 0
        self.win = win
        self.title = CurseString(title)
        self.title.setAttr(curses.A_BOLD)
        self.page = 0
        self.visible = True

    def drawBox(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def update(self, drawSelect=True, to_display=[]):
        if not self.visible:
            return

        page_size = self.getPageSize()
        self.win.erase()
        self.drawBox()

        off = self.page * page_size
        width = self.win.getmaxyx()[1]-2

        self.title.drawToWin(self.win, 0, 1, width) 

        if not to_display and self.source:
            to_display = self.getContent(off, page_size + off)

        for i in range(len(to_display)):
            if i + off == self.selected and drawSelect:
                to_display[i].setAttr(curses.A_STANDOUT)
            to_display[i].drawToWin(self.win, i+1, 1, width)
        self.win.noutrefresh()

    def clear(self, refresh=True):
        self.win.clear()
        if refresh:
            self.win.refresh()

    def toggleVisible(self):
        self.visible = not self.visible
        self.clear()

    def select(self, direction):
        off = self.getPageSize() * self.page
        if direction == Directions.Up:
            self.selected = max(0, self.selected - 1)
            if self.selected < off:
                self.page -= 1
        elif direction == Directions.Down:
            self.selected += 1
            if self.selected > self.source.getMaxIndex():
                self.selected -= 1
            if self.selected >= off + self.getPageSize():
                self.page += 1

    def getSelected(self):
        return self.source.getAtIndex(self.selected)

    def getPageSize(self):
        return self.win.getmaxyx()[0] - 2

    def getContent(self, start, end):
        content = self.source.getItemList(start, end)
        return [CurseString(str(c)) for c in content]

    def next_page(self):
        if self.selected + self.getPageSize() <= self.source.getMaxIndex():
            self.page += 1
            self.selected = self.selected + self.getPageSize()

    def prev_page(self):
        page_incr = max(0, self.page - 1) - self.page
        self.page += page_incr
        self.selected += self.getPageSize() * page_incr


class Application:
    def __init__(self, stdscr):
        self.scr = screen.Screen(stdscr)

        self.contentWindow = Window(self.scr.contentWin, "Videos")

        self.playlistWindow = Window(self.scr.playlistsWin, "Playlists")
        self.playlistWindow.source = youtube.PlaylistList()
        self.getPlaylist()

        self.playerWindow = Window(self.scr.playerWin, "Player Information")
        self.playerWindow.selected = -1

        self.optionWindow = Window(self.scr.optionWin, "Options")
        self.optionWindow.selected = -1

        self.informationWindow = Window(self.scr.informationWin, "Informations")

        self.windowsList = [self.playlistWindow, self.contentWindow]
        self.currentWindow = 0

        self.searchWindow = Window(self.scr.searchWin, "Search")
        self.inSearch = False
        self.textbox = textbox.Textbox(self.scr.searchField)

        self.addToPlaylistWindow = Window(self.scr.addPlaylistWin, "Add to playlist")
        self.addToPlaylistWindow.source = self.playlistWindow.source
        self.addToPlaylistWindow.toggleVisible()  # make window invisible
        self.inAddToPlaylist = False

        self._videoMode = False  # should the video be played alongside the audio
        self.createPlayer()
        self.videoMode = False  # should the video be played alongside the audio
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
        self.searchWindow.update()
        self.textbox.reset()
        self.textbox.edit(update=self.update)
        search_term = self.textbox.gather()
        if search_term:
            self.searchWindow.content = [CurseString(search_term)]
            self.contentWindow.source = youtube.Search(search_term)
            self.currentWindow = 1
        self.searchWindow.clear()
        self.inSearch = False
        self.update()

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
        self.playlistWindow.update()
        self.contentWindow.update()
        self.drawPlayer()
        self.drawOptions()
        self.drawInfo()
        self.drawAddToPlaylist()

        # checking if there is something playing
        if self.inPlaylist and self.player.is_song_finished():  # the current song has finished
            self.next()

        if self.inSearch:
            self.searchWindow.update()

        self.scr.update()


    def drawInfo(self):
        currSelection = self.contentWindow.getSelected()
        content = []
        content.append(CurseString(f"Title: {currSelection.title}"))
        content.append(CurseString(f"Author: {currSelection.author}"))
        self.informationWindow.update(drawSelect=False, to_display=content)

    def drawOptions(self):
        content = []

        content.append(CurseString(f"Auto: {self.inPlaylist}"))
        content.append(CurseString(f"Repeat: {self.repeat}"))
        content.append(CurseString(f"Shuffle: {'on' if self.shuffled else 'off'}"))
        content.append(CurseString(f"Volume : {self.volume:02d} / 100"))
        content.append(CurseString(f"Mode: {'Video' if self.videoMode else 'Audio'}"))
        self.optionWindow.update(drawSelect=False, to_display=content)

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

        self.playerWindow.update(drawSelect=False, to_display=content)

    def drawAddToPlaylist(self):

        if not self.addToPlaylistWindow.visible:
            return

        currSelection = self.contentWindow.getSelected()
        content = []

        for p in self.playlistWindow.source.elements:
            if currSelection in p:
                checkbox = "[x]"
            else:
                checkbox = "[ ]"
            content.append(CurseString(f"{checkbox} {p.title}"))

        self.addToPlaylistWindow.update(to_display=content)

    def select(self, direction):
        if direction == Directions.Up or direction == Directions.Down:
            self.getCurrentWindow().select(direction)
        elif direction == Directions.Left:
            self.currentWindow = max(0, self.currentWindow - 1)
        elif direction == Directions.Right:
            self.currentWindow = min(len(self.windowsList) - 1, self.currentWindow + 1)

        if direction in [Directions.Left, Directions.Right] and self.getCurrentWindow() == self.contentWindow:
            self.getPlaylist()
            self.contentWindow.selected = 0

    def setPlaylist(self):
        if not self.inPlaylist:
            self.playlist = self.playlistWindow.getSelected()
            self.shuffled = False
            self.playlist.currentIndex = self.contentWindow.selected
            self.player.stop()
            self.play(self.playlist.getCurrent())
        self.inPlaylist = not self.inPlaylist

    def getPlaylist(self):
        self.contentWindow.source = self.playlistWindow.getSelected()

    def addToPlaylist(self):
        self.inAddToPlaylist = True
        self.addToPlaylistWindow.toggleVisible()

    def editPlaylist(self):
        currSelection = self.contentWindow.getSelected()
        currPlaylist = self.addToPlaylistWindow.getSelected()
        if currSelection in currPlaylist:
            currPlaylist.remove(currSelection)
        else:
            currPlaylist.add(currSelection)
        self.inAddToPlaylist = False
        self.addToPlaylistWindow.toggleVisible()

    def getCurrentWindow(self):
        if self.inAddToPlaylist:
            return self.addToPlaylistWindow
        else:
            return self.windowsList[self.currentWindow]

    def enter(self):
        if self.getCurrentWindow() == self.playlistWindow:
            self.getPlaylist()
            self.currentWindow = 1
        elif self.getCurrentWindow() == self.addToPlaylistWindow:
            self.editPlaylist()
        else:
            if self.inPlaylist:
                self.playlist.setEffectiveIndex(self.contentWindow.selected)
            self.play()

    def escape(self):
        if self.getCurrentWindow() == self.addToPlaylistWindow:
            self.inAddToPlaylist = False
            self.addToPlaylistWindow.toggleVisible()

    def reload(self):
        self.contentWindow.source.reload()

    def next(self):
        if self.inPlaylist:
            if self.playlist.currentIndex > self.playlist.size:
                self.player.stop()
            else:
                self.play(self.playlist.next())
        else:
            win = self.contentWindow
            win.select(Directions.Down)
            self.play()

    def prev(self):
        if self.inPlaylist:
            if self.playlist.currentIndex > 0:
                self.play(self.playlist.prev())
            else:
                self.player.stop()
        else:
            win = self.contentWindow
            win.select(Directions.Up)
            self.play()

    def nextPage(self):
        self.getCurrentWindow().next_page()

    def prevPage(self):
        self.getCurrentWindow().prev_page()

    def play(self, to_play=youtube.Video()):
        selected = self.contentWindow.getSelected()
        if not to_play.id and selected.id != self.playing.id:
            to_play = selected
        url = to_play.getUrl(self.videoMode)
        self.player.play(url)
        self.playing = to_play

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
        if self.volume < 0:
            self.volume = 0
        elif self.volume > 100:
            self.volume = 100

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
