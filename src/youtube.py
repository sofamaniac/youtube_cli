# -*- coding: utf-8 -*-
import logging
import asyncio

from urllib.parse import urlparse
from urllib.parse import parse_qs
from time import time
import google.auth.exceptions
import googleapiclient.errors

from playlist import Playlist, Playable
from sponsorblockWrapper import SponsorBlock
from youtube_api import *

log = logging.getLogger(__name__)

youtube = Youtube()
MAX_RESULTS = 50
sponsorBlock = SponsorBlock()


class Video(Playable):
    def __init__(self, id="", title="", description="", author="", playlistItemId=""):
        super().__init__(title, author, id)
        self.description = description
        self.playlistItemId = playlistItemId  # useful for editing playlist
        self.skipSegments = []
        self.skipSegmentsDone = False
        self.audio_url = ""
        self.video_url = ""
        self.segmentTask = None

    def mpris_url(self):
        return f"youtu.be/{self.id}"

    async def fetch_url(self, video=False):
        log.info(f"Fetching url for video {self.title}({self.id})")
        await self.get_url(video)

    def url_by_mode(self, video=False):
        if video:
            return self.video_url
        return self.audio_url

    async def _get_url(self, format="best"):

        log.info(f"Fetching url for {self.title}")

        sort = ""  # sort to be applied to the results

        command = f"yt-dlp --no-warnings --format {format} {sort} --print urls --no-playlist https://youtu.be/{self.id}"
        log.info(f"Running {command}")
        proc = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        [urls, stderr], _ = await asyncio.gather(
            proc.communicate(), self.get_skip_segment()
        )
        urls = urls.decode().splitlines()
        if urls:
            return urls[0]
        else:
            return ""

    async def get_url(self, video=False):
        """Return the url for the audio stream of the video"""

        url = self.url_by_mode(video)
        if url:
            # checking if url has expired
            parsed_url = urlparse(url)
            expire = int(parse_qs(parsed_url.query)["expire"][0])
            if expire < time():
                return url

        self.video_url, self.audio_url = await asyncio.gather(
            self._get_url("best"), self._get_url("bestaudio/best")
        )
        log.info(f"Obtained urls for {self.title} ({self.id})")

        return self.url_by_mode(video)

    async def get_skip_segment(self):
        log.info(f"Gathering skip segments for {self.id}")
        self.skipSegments = await sponsorBlock.get_skip_segments(self.id)
        self.skipSegmentsDone = True

    async def check_skip(self, time):
        for skip in self.skipSegments:
            if skip.start <= time <= skip.end:
                return skip.end
        return False


class YoutubeList(Playlist):
    def __init__(self):
        super().__init__()
        self.current_index = 0
        self.next_page = None
        self.prev_page = None

        self.nb_loaded = 0
        self.elements = []
        self.size = 0

    def __contains__(self, item):
        if type(item) is Video:
            item = item.id

        # to gain time we avoid as much as possible api calls
        for v in self.elements:
            if v.id == item:
                return True
        while self.next_page is not None:
            last_index = len(self.elements) - 1
            self.load_next_page()
            for v in self.elements[last_index:]:
                if v.id == item:
                    return True
        return False

    def request(self, who, **what):
        try:
            if who(**what) is not None:
                result = who(**what).execute()
            else:
                return None
        except google.auth.exceptions.RefreshError:
            youtube.get_authenticated_service(refresh=True)
            result = who(**what).execute()
            log.warning("Error with request")
        return result

    async def _load_next_page(self):
        pass

    async def load_next_page(self):
        await self._load_next_page()

    def update_tokens(self, response):
        self.next_page = (
            response["nextPageToken"] if "nextPageToken" in response else None
        )
        self.prev_page = (
            response["prevPageToken"] if "prevPageToken" in response else None
        )

    async def get_at_index(self, index):
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""

        while index > self.nb_loaded and self.next_page is not None:
            await self.load_next_page()
        if self.nb_loaded == 0:
            await self.load_next_page()
        if self.nb_loaded > index >= self.nb_loaded:
            log.warning("index greater than size")
            return self.elements[-1]
        elif index >= self.nb_loaded:
            return None
        return self.elements[index]

    async def get_item_list(self, start, end):
        while end + 1 > self.nb_loaded and self.next_page is not None:
            await self.load_next_page()
        max_index = min(end, self.nb_loaded)
        return self.elements[start:max_index]

    async def load_all(self):
        while self.next_page is not None or self.nb_loaded == 0:
            await self.load_next_page()
        self.size = self.nb_loaded

    async def reload(self):
        self.nb_loaded = 0
        # self.size = 0  # not necessary I think
        self.elements = []
        self.next_page = None
        self.prev_page = None

        await self.load_next_page()

    async def get_max_index(self):
        return self.nb_loaded - 1


class YoutubePlaylist(YoutubeList):
    def __init__(self, id, title, nb_videos):

        super().__init__()
        self.title = title
        self.id = id
        self.size = nb_videos
        self.order = [i for i in range(self.size)]  # used for shuffling
        self.api_object = youtube.playlist_items

    async def init(self):
        await self.load_next_page()  # we load the first page

    def _add_videos(self, id_list):

        to_request = "id, snippet, status, contentDetails"
        video_id_list = [v[0] for v in id_list]
        args = {
            "part": to_request,
            "id": ",".join(video_id_list),
        }
        try:
            response = self.request(youtube.videos.list, **args)
        except googleapiclient.errors.HttpError:
            log.critical("Error while adding videos to playlist")

        nb_added = 0
        for i, v in enumerate(response["items"]):
            if not self.check_video_availability(v):
                self.removeMax()
                continue
            self.elements.append(
                Video(
                    v["id"],
                    v["snippet"]["title"],
                    v["snippet"]["description"],
                    v["snippet"]["channelTitle"],
                    id_list[i][1]  # playlist_items_id
                    # TODO: not sure if order is preserved
                )
            )
            nb_added += 1
        return nb_added

    def check_video_availability(self, video):
        # this condition is maybe too strong as it excludes non-repertoriated
        result = video["status"]["privacyStatus"] == "public"
        if "regionRestriction" in video["contentDetails"]:
            t = video["contentDetails"]["regionRestriction"]
            if "blocked" in t:
                result = result and "FR" not in t["blocked"]
            else:
                result = result and "FR" in t["allowed"]
        return result

    async def _load_next_page(self):
        to_request = "id, snippet, status, contentDetails"
        args = {
            "part": to_request,
            "playlistId": self.id,
            "maxResults": MAX_RESULTS,
            "pageToken": self.next_page,
        }
        try:
            response = self.request(self.api_object.list, **args)
        except googleapiclient.errors.HttpError:
            log.critical("Error when querying playlist")

        idList = []
        for v in response["items"]:
            idList.append((v["snippet"]["resourceId"]["videoId"], v["id"]))
        self.nb_loaded += self._add_videos(idList)
        self.update_tokens(response)

    def add(self, video):
        args = {
            "part": "snippet",
            "body": {
                "snippet": {
                    "playlistId": self.id,
                    "resourceId": {"kind": "youtube#video", "videoId": video.id},
                },
                "position": 0,
            },
        }
        try:
            self.request(self.api_object.insert, **args)
        except googleapiclient.errors.HttpError:
            log.critical("Error while adding video to playlist")
        self.reload()  # we refresh the content

    def remove(self, video):
        playlistItemId = ""
        for v in self.elements:
            if v.id == video.id:
                playlistItemId = v.playlistItemId
                break
        try:
            self.request(self.api_object.delete, id=playlistItemId)
        except googleapiclient.errors.HttpError:
            log.critical("Error while removing video from playlist")
        self.reload()

    def removeMax(self):
        if not self.order:
            return
        index_max = max(range(len(self.order)), key=self.order.__getitem__)
        if self.order[index_max] >= self.size:
            self.order.pop(index_max)
            self.removeMax()  # Hopefully it will never go deep


class LikedVideos(YoutubePlaylist):
    def __init__(self, title):

        super().__init__("Liked", title, 0)
        self.api_object = youtube.videos

    def is_loaded(self):
        return self.next_page is None

    async def load_all(self):
        await super().load_all()
        self.order = [i for i in range(self.size)]
        if self.shuffled:
            await self.shuffle()

    async def _load_next_page(self):
        to_request = "id, snippet, status, contentDetails"
        args = {
            "part": to_request,
            "myRating": "like",
            "maxResults": MAX_RESULTS,
            "pageToken": self.next_page,
        }
        try:
            response = self.request(youtube.videos.list, **args)
        except googleapiclient.errors.HttpError:
            log.critical("Error while loading liked videos")
            return

        if not response:
            return

        idList = []
        for v in response["items"]:
            idList.append((v["id"], ""))
        nb_loaded = self._add_videos(idList)

        self.size += nb_loaded
        self.nb_loaded += nb_loaded
        self.update_tokens(response)

    async def next(self):
        self.current_index += 1
        while self.current_index >= self.size and self.is_loaded():
            await self.load_next_page()
        if self.current_index >= self.size and self.is_loaded():
            return Playable()
        shuffled_index = self.order[self.current_index]
        return await self.get_at_index(shuffled_index)

    async def shuffle(self):
        await self.load_all()
        await YoutubePlaylist.shuffle(self)

    async def get_max_index(self):
        if not self.is_loaded():
            return 1e99
        else:
            return self.size - 1

    def add(self, video):
        try:
            self.request(self.api_object.rate, id=video.id, rating="like")
        except googleapiclient.errors.HttpError:
            log.critical("Error while adding videos to liked videos")
        self.reload()  # we refresh the content

    def remove(self, video):
        try:
            self.request(self.api_object.rate, id=video.id, rating="none")
        except googleapiclient.errors.HttpError:
            log.critical("Error while removing like from video")
        self.reload()  # we refresh the content


class YoutubePlaylistList(YoutubeList):
    def __init__(self):
        super().__init__()
        self.elements = [LikedVideos("Liked Videos")]
        self.nb_loaded = 1
        self.api_object = youtube.playlists

    async def init(self):

        await self.load_next_page()
        await self.load_all()

        await self.elements[0].load_all()

    async def _load_next_page(self):
        args = {
            "part": "id, snippet, contentDetails",
            "maxResults": MAX_RESULTS,
            "mine": True,
            "pageToken": self.next_page,
        }
        try:
            response = self.request(self.api_object.list, **args)
        except googleapiclient.errors.HttpError:
            log.critical("Error while loading list of playlists")

        if not response:
            return

        for p in response["items"]:
            self.elements.append(
                YoutubePlaylist(
                    p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"]
                )
            )
        self.update_tokens(response)
        self.nb_loaded += len(response["items"])
        if self.next_page is None:
            self.size = self.nb_loaded

    async def shuffle(self):
        return

    async def unshuffle(self):
        return


class Search(YoutubePlaylist):
    def __init__(self, query):

        super().__init__()
        self.query = query
        self.size = 1e99
        self.api_object = youtube.search

        self.load_next_page()

    async def _load_next_page(self):

        args = {
            "part": "id, snippet, contentDetails",
            "maxResults": MAX_RESULTS,
            "pageToken": self.next_page,
            "q": self.query,
            "type": "video",
        }

        try:
            response = self.request(self.api_object.list, **args)
        except googleapiclient.errors.HttpError:
            log.critical("Error while searching for videos")

        id_list = []
        for v in response["items"]:
            id_list.append((v["id"]["videoId"], ""))

        self.nb_loaded += self._add_videos(id_list)
        self.update_tokens(response)

        if self.next_page is None:
            self.size = self.nb_loaded

    async def shuffle(self):
        return

    async def unshuffle(self):
        return
