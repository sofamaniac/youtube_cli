import youtube
import screen

from screen import Directions
import curses
import textbox
import mpv

import time
import sys

import locale

class Message():
    
    def __init__(self, title, *kwargs):
        self.title = title


class Window():

    def __init__(self, win, title, page_size, yt):
        self.source = None
        self.selected = 0
        self.win = win
        self.title = title
        self.page = 0
        self.page_size = page_size
        self.yt = yt

    def drawBox(self, color=screen.COLOR_BORDER):
        self.win.attrset(curses.color_pair(color))
        self.win.box()
        self.win.attrset(0)

    def addstr(self, y, x, s, **kwargs):
        width = self.win.getmaxyx()[1] - 2
        attr = kwargs.pop("attr", 0)    # if key exist return its value otherwise 0
        color = kwargs.pop("color", screen.COLOR_TEXT)
        
        # ensuring the string fit in the window
        s = s.encode('utf-8')

        # get length of s by counting number of starting bytes
        # SO related link https://stackoverflow.com/a/4063229
        l = 0
        for b in s:
            l += 1 if (b & 0xc0) != 0x80 else 0
        if l > width:
            # if the string is too long we cut at the first starting byte that makes it short enough
            i = width - 3
            while i > 0 and s[i] & (0xc0) == 0x80:
                i -= 1
            s = s[:i] + b"..."

        self.win.addstr(y, x, s, attr | curses.color_pair(color))
    
    def update(self, drawSelect=True, to_display=[]):
        self.win.erase()
        self.drawBox()
        self.page_size = self.win.getmaxyx()[0]-2  # update page size when resize

        off = self.page*self.page_size

        self.addstr(0, 1, self.title, attr=curses.A_BOLD)

        if not to_display and self.source:
            to_display = self.source.getItemList(off, self.page_size+off)

        for i in range(len(to_display)):
            if i+off == self.selected and drawSelect:
                self.addstr(i+1, 1, to_display[i].title, attr=curses.A_STANDOUT)
            else:
                self.addstr(i+1, 1, to_display[i].title)
        self.win.noutrefresh() 

    def select(self, direction):
        off = self.page_size*self.page
        if direction == Directions.Up:
            self.selected= max(0, self.selected-1)
            if self.selected < off:
                self.page -= 1
        elif direction == Directions.Down:
            #self.selected= min(len(self.content) -1, self.selected+1)
            # TODO find condition maybe ?
            self.selected += 1
            if self.selected > self.source.getMaxIndex():
                self.selected -= 1
            if self.selected >= off + self.page_size:
                self.page += 1

    def getSelectId(self):
        if self.selected < len(self.content) and "id" in self.content[self.selected]:
            return self.content[self.selected].id
        else:
            # TODO: proper error handling
            return -1

    def getSelected(self):
        return self.source.getItem(self.selected)

class Application():

    def __init__(self, stdscr):
        self.yt  = youtube.YoutbeHandler()
        self.yt.start()
        self.scr = screen.Screen(stdscr)

        self.contentWindow = Window(self.scr.contentWin, "Videos", screen.CONTENT_HEIGHT-2, self.yt)
        self.playlistWindow = Window(self.scr.playlistsWin, "Playlists", screen.PLAYLIST_HEIGHT-2, self.yt)

        self.playerWindow = Window(self.scr.playerWin, "Player Information", screen.PLAYER_HEIGHT-2, None)
        self.playerWindow.selected = -1

        self.optionWindow = Window(self.scr.optionWin, "Options", screen.OPTION_HEIGHT-2, None)
        self.optionWindow.selected = -1

        self.informationWindow = Window(self.scr.informationWin, "Informations", screen.INFO_HEIGHT-2, None)

        self.windowsList = [self.playlistWindow, self.contentWindow]
        self.currentWindow = 0

        self.searchWindow = Window(self.scr.searchWin, "Search", 3, None)
        self.textWindow = self.searchWindow.win.subwin(1, 78, 11, 11)  # begin_x/y are relative to the SCREEN not the parent window
        self.inSearch = False
        self.textbox = textbox.Textbox(self.textWindow)

        self.player = mpv.MPV(video=False, ytdl=True)
        self.playing = {'title': 'None', 'id': ''}

        self.playlistWindow.source = youtube.PlaylistList()
        self.getPlaylist()
        
        self.inPlaylist = False
        self.playlist = []
        self.playlistIndex = 0
        self.inRepeat = False

        self.volume = 100
        self.isMuted = False

        locale.setlocale(locale.LC_ALL, '')

    def update(self):

        # Drawing all the windows
        self.playlistWindow.update()
        self.contentWindow.update() 
        self.drawPlayer()
        self.drawOptions()
        self.drawInfo()

        self.scr.update()

        # checking if there is something playing
        if self.inPlaylist and not self.player._get_property("media-title"): # the current song has finished
            self.next()

        if self.inSearch:
            self.searchWindow.update()
            self.textbox.reset()
            self.textbox.edit()
            search_term = self.textbox.gather()
            self.searchWindow.content = [{"content": search_term}]
            self.contentWindow.title = search_term
            self.inSearch = False
            
    def drawInfo(self):
        currSelection = self.contentWindow.getSelected()
        content = []
        content.append(Message(f"Title: {currSelection.title}"))
        content.append(Message(f"Duration: 0"))
        content.append(Message(f"Author: {currSelection.author}"))
        self.informationWindow.update(drawSelect=False, to_display=content)

    
    def drawOptions(self):
        # TODO use messages
        content = []

        content.append(Message(f"Auto: {self.inPlaylist}"))
        content.append(Message(f"Repeat: {self.inRepeat}"))
        content.append(Message("Volume : {:02d} / 100".format(self.volume)))
        self.optionWindow.update(drawSelect=False, to_display=content)

    def drawPlayer(self):
        # TODO use messages
        currContent = [self.player._get_property("media-title"), self.player._get_property("duration")]
        title = self.playing['title']
        dur = currContent[1]

        time_pos = self.player._get_property("time-pos")

        t = time.strftime("%H:%M:%S", time.gmtime(time_pos))
        d = time.strftime("%H:%M:%S", time.gmtime(dur))

        t = t if time_pos else "00:00:00"
        d = d if dur else "00:00:00"
        content = [Message(f"{title} - {t}/{d}")]

        # drawing progress bar
        time_pos = time_pos if time_pos else 0
        dur = dur if dur else 0
        frac_time = time_pos / (dur+1)
        width = screen.PLAYER_WIDTH - 5 - len(" {}/{}".format(t, d))
        bar = "\u2588"*int(frac_time*width)
        space = "-"*(width - len(bar))
        progress = "|" + bar + space + "|" + " {}/{}".format(t, d)
        content.append(Message(progress))

        self.playerWindow.update(drawSelect=False, to_display=content)


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
        self.player.playlist_clear()
        if not self.inPlaylist:
            self.playlist = []
            for e in self.contentWindow.content:
                self.playlist.append(e)
            self.playlistIndex = self.contentWindow.selected
            self.player.stop()
            self.play(self.playlist[self.playlistIndex])
        self.inPlaylist = not self.inPlaylist

    def getPlaylist(self):
        self.contentWindow.source = self.playlistWindow.getSelected()
    
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
            self.playlistIndex += 1
            if self.playlistIndex > len(self.playlist):
                self.player.stop()
            else:
                self.play(self.playlist[self.playlistIndex])
        else:
            win = self.contentWindow
            win.select(Directions.Down)
            self.play()

    def prev(self):
        if self.inPlaylist:
            if self.playlistIndex > 0:
                self.playlistIndex -= 1
                self.play(self.playlist[self.playlistIndex])
            else:
                self.player.stop()
        else:
            win = self.contentWindow
            win.select(Directions.Up)
            self.play()

    def next_page(self):
        # TODO rework to avoid getting past the last page
        win = self.windowsList[self.currentWindow]
        win.page += 1
        win.selected = win.selected + win.page_size

    def prev_page(self):
        win = self.windowsList[self.currentWindow]
        page_incr = max(0, win.page-1) - win.page
        win.page += page_incr
        win.selected += win.page_size*page_incr

    def play(self, to_play=youtube.Video("", "", "", "")):
        next = self.contentWindow.getSelected()
        if to_play.id != "":
            url = to_play.getUrl()
            self.player.play(url)
            self.playing['id'] = next
            self.playing['title'] = to_play.title
        elif next != self.playing['id']:
            to_play = self.contentWindow.getSelected()
            url = to_play.getUrl()
            self.player.play(url)
            self.playing['id'] = next
            self.playing['title'] = to_play.title

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

    def quit(self):
        self.yt.terminate()
        self.yt.join()

