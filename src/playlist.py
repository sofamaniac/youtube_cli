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

    async def get_url(self, video=False) -> str:
        return self.title

    async def load_url(self, video=False) -> str:
        return self.get_url(video)

    async def mpris_url(self) -> str:
        return self.title

    async def check_skip(self, time) -> bool:
        return False


class Playlist:
    def __init__(self):
        self.current_index = 0
        self.nextPage = None
        self.prevPage = None

        self.elements = []
        self.size = 0
        self.order = []
        self.title = ""
        self.shuffled = False

    def __contains__(self, item: Playable) -> bool:

        # to gain time we avoid as much as possible api calls
        for v in self.elements:
            if v == item:
                return True
        return False

    async def get_at_index(self, index: int):
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""
        if index >= self.size > 0:
            return self.elements[-1]
        elif self.size == 0:
            return None
        return self.elements[index]

    async def get_item_list(self, start: int, end: int) -> list[Playable]:
        """Returns the elements between indexes [start](included) and [end](excluded)"""
        max_index = min(end, self.size)
        return self.elements[start:max_index]

    async def get_video_url(self, index: int):
        """returns the element at [index] url"""
        return await self.get_at_index(index).getUrl()

    async def shuffle(self):
        self.order = list(range(self.size))
        shuffle(self.order)
        self.shuffled = True

    async def unshuffle(self):
        self.order = list(range(self.size))
        self.shuffled = False

    async def next(self) -> Playable:
        if self.current_index >= self.size:
            return Playable()
        self.current_index += 1
        shuffled_index = self.order[self.current_index]
        return await self.get_at_index(shuffled_index)

    async def prev(self) -> Playable:
        if self.current_index == 0:
            return Playable()
        self.current_index -= 1
        shuffled_index = self.order[self.current_index]
        return await self.get_at_index(shuffled_index)

    async def get_current(self) -> Playable:
        shuffled_index = self.order[self.current_index]
        return await self.get_at_index(shuffled_index)

    async def get_next(self) -> Playable:
        index = (self.current_index + 1) % self.size
        shuffled_index = self.order[index]
        return await self.get_at_index(shuffled_index)

    async def get_current_index(self) -> Playable:
        if self.current_index >= self.size:
            self.current_index = self.size - 1
        return self.order[self.current_index]

    async def get_max_index(self) -> int:
        return self.size - 1

    async def set_effective_index(self, index):
        self.current_index = 0
        while (
            self.current_index < self.size and self.order[self.current_index] != index
        ):
            self.current_index += 1

    async def search(self, query: str) -> int:
        """Search for [query] in the title of the playlist element.
        If a match is found, returns its index in the playlist,
        otherwise returns None"""
        for i, e in enumerate(self.elements):
            if query in e.title:
                return i
        return None

    def __str__(self):
        return self.title


class PlaylistList:
    def __init__(self):

        self.elements = []
        self.size = 0

    def add_playlist(self, p: Playable):
        """Add [p] to the playlist"""
        self.elements.append(p)
        self.size += 1

    async def get_at_index(self, index: int) -> Playlist:
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""
        if index >= self.size:
            return self.elements[-1]
        return self.elements[index]

    async def get_item_list(self, start, end) -> list[Playlist]:
        max_index = min(end, self.size)
        return self.elements[start:max_index]

    async def get_max_index(self) -> int:
        return self.size - 1
