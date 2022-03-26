from playlist import *
from os import walk
from os.path import join as joinpath

import eyed3

class LocalFile(Playable):
    def __init__(self, title, author, path):

        Playable.__init__(self, title, author, path)
        self.path = path

    def getUrl(self, video=False):
        return self.path

class Folder(Playlist):

    def __init__(self, path):
        Playlist.__init__(self)

        self.path = path
        self.loadFiles()
        self.title = path

    def loadFiles(self):

        self.elements = []

        for dirpath, _, filenames in walk(self.path):
            for f in filenames:
                path = joinpath(dirpath, f)
                audioFile = eyed3.load(path)
                if audioFile:
                    tag = audioFile.tag
                    if tag:
                        artist = tag.artist
                        title = tag.title
                    artist = artist if artist else "unknown"
                    title = title if title else f
                    self.elements.append(LocalFile(title, artist, path))

        self.size = len(self.elements)

class FolderList(Playlist):

    def __init__(self):
        Playlist.__init__(self)

        self.foldersPaths = ["/home/sofamaniac/Musics/"]
        self.elements = []

        for p in self.foldersPaths:
            self.elements.append(Folder(p))
        self.size = len(self.elements)





