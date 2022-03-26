from random import shuffle

class Playable:

    def __init__(self, title="", author="", id=None):
        self.title = title
        self.author = author
        if not id:
            self.id = self.title
        else:
            self.id = id

    def __equal__(self, other):
        if isinstance(other, Playable):
            return self.id == other.id
        return False
    
    def __str__(self):
        return self.title

    def getUrl(self, video=False):
        return self.title

    def checkSkip(self, time):
        return False

class Playlist:

    def __init__(self):
        self.currentIndex = 0
        self.nextPage = None
        self.prevPage = None

        self.elements = []
        self.size = 0
        self.order = []
        self.title = ""

    def __contains__(self, item:Playable):

        # to gain time we avoid as much as possible api calls
        for v in self.elements:
            if v == item:
                return True
        return False

    def getAtIndex(self, index):
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""
        if index >= self.size:
            return self.elements[-1]
        return self.elements[index]

    def getItemList(self, start, end):
        max_index = min(end, self.size)
        return self.elements[start:max_index]

    def getVideoUrl(self, index):
        return self.getAtIndex(index).getUrl()

    def shuffle(self):
        self.order = [i for i in range(self.size)]
        shuffle(self.order)

    def unshuffle(self):
        self.order = [i for i in range(self.size)]

    def next(self):
        if self.currentIndex >= self.size:
            return Playable()
        self.currentIndex += 1
        shuffled_index = self.order[self.currentIndex]
        return self.getAtIndex(shuffled_index)

    def prev(self):
        if self.currentIndex == 0:
            return Playable()
        self.currentIndex -= 1
        shuffled_index = self.order[self.currentIndex]
        return self.getAtIndex(shuffled_index)

    def getCurrent(self):
        shuffled_index = self.order[self.currentIndex]
        return self.getAtIndex(shuffled_index)

    def getMaxIndex(self):
        return self.size - 1

    def setEffectiveIndex(self, index):
        self.currentIndex = 0
        while self.currentIndex < self.size and self.order[self.currentIndex] != index:
            self.currentIndex += 1

    def __str__(self):
        return self.title


class PlaylistList():

    def __init__(self):

        self.elements = []
        self.size = 0

    def addPlaylist(self, p):
        self.elements.append(p)
        self.size += 1

    def getAtIndex(self, index):
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""
        if index >= self.size:
            return self.elements[-1]
        return self.elements[index]

    def getItemList(self, start, end):
        max_index = min(end, self.size)
        return self.elements[start:max_index]

    def getMaxIndex(self):
        return self.size - 1

