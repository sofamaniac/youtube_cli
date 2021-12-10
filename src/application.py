import youtube
import screen

from screen import Directions
import curses
import mpv

import time

class Window():

    def __init__(self, win, title, fetcher, page_size):
        self.content = []
        self.selected = 0
        self.win = win
        self.title = title
        self.fetcher = fetcher
        self.page = 0
        self.page_size = page_size

    def drawBox(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def addstr(self, y, x, s, attr=0, color=screen.COLOR_TEXT):
        self.win.addstr(y, x, s, attr | curses.color_pair(color))
    
    def update(self, drawSelect=True):
        self.win.erase()
        self.drawBox()

        off = self.page*self.page_size

        self.addstr(0, 1, self.title, attr=curses.A_BOLD)

        for i in range(min(abs(len(self.content) - off), self.page_size)):
            if i+off == self.selected and drawSelect:
                self.addstr(i+1, 1, self.content[i+off][1], curses.A_STANDOUT)
            else:
                self.addstr(i+1, 1, self.content[i+off][1])
        self.win.noutrefresh() 

    def select(self, direction):
        off = self.page_size*self.page
        if direction == Directions.Up:
            self.selected= max(0, self.selected-1)
            if self.selected < off:
                self.page -= 1
        elif direction == Directions.Down:
            self.selected= min(len(self.content) -1, self.selected+1)
            if self.selected >= off + self.page_size:
                self.page += 1

    def getSelectId(self):
        return self.content[self.selected][0]

    def fetch(self, page=None, **kwargs):
        if kwargs:
            self.content = self.fetcher(page, **kwargs)
        else:
            self.content = self.fetcher(page, id=self.getSelectId())


class Application():

    def __init__(self, stdscr):
        self.yt  = youtube.YoutbeHandler()
        self.scr = screen.Screen(stdscr)

        self.contentWindow = Window(self.scr.contentWin, "Videos", self.yt.getPlaylist, screen.CONTENT_HEIGHT-2)
        self.playlistWindow = Window(self.scr.playlistsWin, "Playlists", self.yt.getPlaylistList, screen.PLAYLIST_HEIGHT-2)

        self.playerWindow = Window(self.scr.playerWin, "Player Information", lambda x, **kwargs:None, screen.PLAYER_HEIGHT-2)
        self.playerWindow.selected = -1

        self.windowsList = [self.playlistWindow, self.contentWindow]
        self.currentWindow = 0

        self.player = mpv.MPV(video=False, ytdl=True)
        self.playingId = ""

        self.playlistWindow.fetch(id="")
        self.getPlaylist()

        self.inPlaylist = False
        self.inRepeat = False

        self.volume = 100
        self.isMuted = False

    def update(self):

        for i, w in enumerate(self.windowsList):
            w.update(i == self.currentWindow)
        self.drawPlayer()

        self.scr.update()

    def drawPlayer(self):
        currContent = ["", self.player._get_property("media-title"), self.player._get_property("duration")]
        title = currContent[1]
        dur = currContent[2]

        time_pos = self.player._get_property("time-pos")

        t = time.strftime("%H:%M:%S", time.gmtime(time_pos))
        d = time.strftime("%H:%M:%S", time.gmtime(dur))

        t = t if time_pos else "00:00:00"
        d = d if dur else "00:00:00"
        content = []

        content.append(["", "{} - {}/{}".format(title, t, d)])
        content.append(["", "Auto : {}\t Repeat: {}".format(self.inPlaylist, self.inRepeat)])
        content.append(["", "Volume : {:02d} / 100".format(self.volume)])
        self.playerWindow.content = content
        self.playerWindow.update(drawSelect=False)


    def select(self, direction):
        if direction == Directions.Up or direction == Directions.Down:
            self.windowsList[self.currentWindow].select(direction)
        elif direction == Directions.Left:
            self.currentWindow = max(0, self.currentWindow -1)
        elif direction == Directions.Right:
            self.currentWindow = min(len(self.windowsList) - 1, self.currentWindow +1)

        if (direction == Directions.Left or direction == Directions.Right) \
                and self.getCurrentWindow() == self.contentWindow:
            self.getPlaylist()
            self.contentWindow.selected = 0

    def setPlaylist(self):
        if not self.inPlaylist:
            self.player.playlist_clear()
            self.inPlaylist = True
            for e in self.contentWindow.content:
                self.player.playlist_append("https://youtu.be/{}".format(e[0]))
            self.player.playlist_play_index(self.contentWindow.selected+1)
        else:
            self.player.playlist_clear()
            self.inPlaylist = False

    def getPlaylist(self):
        self.contentWindow.fetch(id=self.playlistWindow.getSelectId())

    def getPlaylistList(self):
        self.playlistWindow.fetch()
    
    def getCurrentWindow(self):
        return self.windowsList[self.currentWindow]
    
    def enter(self):
        if self.getCurrentWindow() == self.playlistWindow:
            self.getPlaylist()
            self.currentWindow = 1
        else:
            self.play()

    def next(self):
        if self.inPlaylist:
            self.player.playlist_next()
        else:
            win = self.contentWindow
            win.select(Directions.Down)
            self.play()

    def prev(self):
        if self.inPlaylist:
            if self.player._get_property("playlist-pos") > 0:
                self.player.playlist_prev()
        else:
            win = self.contentWindow
            win.select(Directions.Up)
            self.play()

    def next_page(self):
        win = self.windowsList[self.currentWindow]
        page_incr = min(win.page+1, len(win.content)// win.page_size) - win.page
        win.page += page_incr
        win.selected = min(win.selected + page_incr*win.page_size, len(win.content))

    def prev_page(self):
        win = self.windowsList[self.currentWindow]
        page_incr = max(0, win.page-1) - win.page
        win.page += page_incr
        win.selected += win.page_size*page_incr

    def play(self):
        next = self.contentWindow.getSelectId()
        if next != self.playingId:
            self.player.play("https://youtu.be/{}".format(self.contentWindow.getSelectId()))
            self.playingId = next

    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.command("cycle", "pause")

    def repeat(self):
        self.inRepeat = not self.inRepeat
        self.player._set_property("loop", "inf" if self.inRepeat else "no")

    def forward(self, dt):
        currentSong = self.player._get_property("media-title")
        if not currentSong:
            return
        self.player.command("seek", "{}".format(dt), "relative")

    def increaseVolume(self, dv):
        self.volume += dv
        if self.volume < 0:
            self.volume = 0
        elif self.volume > 100:
            self.volume = 100
        self.player._set_property("volume", self.volume)

    def mute(self):
        self.isMuted = not self.isMuted
        if self.isMuted:
            self.player._set_property("volume", 0)
        else:
            self.player._set_property("volume", self.volume)

