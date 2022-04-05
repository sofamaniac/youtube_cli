from os import walk
from os.path import join as joinpath

import eyed3

from playlist import Playable, Playlist, PlaylistList


class LocalFile(Playable):
    def __init__(self, title, author, path):

        Playable.__init__(self, title, author, path)
        self.path = path

    def get_url(self, video=False):
        return self.path


class Folder(Playlist):
    def __init__(self, path):
        Playlist.__init__(self)

        self.path = path
        self.title = path
        self.load_files()

    def load_files(self):

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


class FolderList(PlaylistList):
    def __init__(self):
        PlaylistList.__init__(self)

        folder_prefix = "/home/sofamaniac/Musics/"

        folder_suffixes = [
            "",
            "Youtube",
            "soundcloud",
            "How To Train Your Dragon OST",
            "How To Train Tour Dragon 2 OST",
            "Classique",
        ]

        self.foldersPaths = [folder_prefix + s for s in folder_suffixes]

        self.elements = []

        for p in self.foldersPaths:
            self.elements.append(Folder(p))
        self.size = len(self.elements)
