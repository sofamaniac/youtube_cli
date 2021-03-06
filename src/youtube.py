# -*- coding: utf-8 -*-
import os
import pickle
import shlex
from random import shuffle
from threading import Thread, Lock
import subprocess
import time

# === Google API === #
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.exceptions

import logging

from playlist import Playlist, Playable
from property import PropertyObject, Property

log = logging.getLogger(__name__)

MAX_RESULTS = 50


class YoutubeAPIObject:
    def __init__(self, element=None):
        self.element = element

    def list(self, **args):
        return self.element().list(**args)

    def insert(self, **args):
        return self.element().insert(**args)

    def delete(self, **args):
        return self.element().delete(**args)

    def rate(self, **args):
        return self.element().rate(**args)

    def update(self, element):
        self.element = element


class YoutubeVideoAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            super().__init__(youtube.videos)
        else:
            super().__init__()

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.videos)


class YoutubePlaylistItemAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            super().__init__(youtube.playlistItems)
        else:
            super().__init__()

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.playlistItems)


class YoutubePlaylistAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            super().__init__(youtube.playlists)
        else:
            super().__init__()

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.playlists)


class YoutubeSearchAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            super().__init__(youtube.search)
        else:
            super().__init__()

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.search)


class Youtube:
    def __init__(self):

        self.youtube = None
        self.search = YoutubeSearchAPI(self.youtube)
        self.videos = YoutubeVideoAPI(self.youtube)
        self.playlists = YoutubePlaylistAPI(self.youtube)
        self.playlist_items = YoutubePlaylistItemAPI(self.youtube)
        self.get_authenticated_service()

    def get_authenticated_service(self, refresh=False):
        scopes = ["https://www.googleapis.com/auth/youtube"]
        data_path = "data/"
        client_secrets_file = data_path + "client_secret.json"
        api_service_name = "youtube"
        api_version = "v3"
        path = data_path + "CREDENTIALS_PICKLE_FILE"
        if not refresh and os.path.exists(path):
            with open(path, "rb") as f:
                credentials = pickle.load(f)
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            credentials = flow.run_local_server()
            with open(path, "wb") as f:
                pickle.dump(credentials, f)
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials
        )
        self.search.update(self.youtube)
        self.videos.update(self.youtube)
        self.playlists.update(self.youtube)
        self.playlist_items.update(self.youtube)


youtube = Youtube()

# ================== #


# === SponsorBlock === #
import sponsorblock as sb
from multiprocessing import Process, Queue, Manager

queue = Queue()


class TimeoutException(Exception):
    pass


import jsonpickle


class SponsorBlockCache:
    def __init__(self, path="data/sponsorBlock.cache"):

        self.path = path
        with open(path, "r") as f:
            self.data = jsonpickle.decode(f.read())

    def add_entry(self, video_id, block_list):

        if video_id in self.data and self.data[video_id] == block_list:
            return

        self.data[video_id] = block_list
        with open(self.path, "w") as f:
            f.write(jsonpickle.encode(self.data))

    def query(self, video_id):

        if video_id in self.data:
            return self.data[video_id]
        else:
            return None


class SponsorBlock(PropertyObject):
    """Class to handle sponsor block"""

    def __init__(self):
        super().__init__()
        self.cache = SponsorBlockCache()
        self.client = sb.Client()
        self.enableSponsorBlock = None
        self._add_property("enableSponsorBlock", True)
        self.timeoutSponsorBlock = 5  # timeout in seconds
        self._add_property("timeoutSponsorBlock", 5)
        self.toSkipSponsorBlock = ["sponsor", "selfpromo", "music_offtopic"]
        self._add_property("toSkipSponsorBlock", self.toSkipSponsorBlock)

    def get_skip_segments(self, video_id=""):

        if not self.enableSponsorBlock:
            return []

        tmp = self.cache.query(video_id)

        if tmp:
            return tmp
        else:
            block_list = []
            block_list = self.run_with_timeout(video_id)
            self.cache.add_entry(video_id, block_list)
            return block_list

    def query_servers(self, video_id=""):
        block_list = []
        try:
            block_list = self.client.get_skip_segments(
                video_id=video_id, categories=self.toSkipSponsorBlock
            )
        except (
            TimeoutException,
            sb.errors.NotFoundException,
            sb.errors.ServerException,
            sb.errors.ServerException,
        ) as _:
            block_list = []
        queue.put(block_list)

    def run_with_timeout(self, video_id=""):
        # First we ensure the queue we are using is empty
        while not queue.empty():
            queue.get()
        p = Process(target=self.query_servers, kwargs={"video_id": video_id})
        p.start()
        p.join(self.timeoutSponsorBlock)
        if p.is_alive():
            p.terminate()
            raise TimeoutException
        else:
            result = queue.get()
            return result


sponsorBlock = SponsorBlock()


# ============================= #

from urllib.parse import urlparse
from urllib.parse import parse_qs
from time import time, sleep


class Video(Playable):
    def __init__(self, id="", title="", description="", author="", playlistItemId=""):
        super().__init__(title, author, id)
        self.description = description
        self.playlistItemId = playlistItemId  # useful for editing playlist
        self.skipSegments = []
        self.skipSegmentsDone = False
        self.audio_url = ""
        self.video_url = ""

    def fetch_url(self, video=False):
        thread = Thread(target=self.get_url, kwargs={"video": video}, daemon=True)
        thread.start()

    def url_by_mode(self, video=False):
        if video:
            return self.video_url
        return self.audio_url

    def _get_url(self, format="best"):

        sort = ""  # sort to be applied to the results

        command = f"yt-dlp --no-warnings --format {format} {sort} --print urls --no-playlist https://youtu.be/{self.id}"
        urls = subprocess.run(shlex.split(command), capture_output=True, text=True)
        urls = urls.stdout.splitlines()
        if urls:
            self.get_skip_segment()
            return urls[0]
        else:
            return ""

    def get_url(self, video=False):
        """Return the url for the audio stream of the video"""

        url = self.url_by_mode(video)
        if url:
            # checking if url has expired
            parsed_url = urlparse(url)
            expire = int(parse_qs(parsed_url.query)["expire"][0])
            if expire < time():
                return url

        self.video_url = self._get_url("best")
        self.audio_url = self._get_url("bestaudio/best")

        return self.url_by_mode(video)

    def get_skip_segment(self):
        try:
            self.skipSegmentsDone = True
            self.skipSegments = sponsorBlock.get_skip_segments(self.id)
        except (TimeoutException) as _:
            log.warning("SponsorBlock timed out")
            self.skipSegments = []

    def check_skip(self, time):
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

        self.is_loading = Lock()

    def __contains__(self, item):
        if type(item) is Video:
            item = item.id

        # to gain time we avoid as much as possible api calls
        for v in self.elements:
            if v.id == item:
                return True
        while self.next_page != None:
            last_index = len(self.elements) - 1
            self.load_next_page()
            for v in self.elements[last_index:]:
                if v.id == item:
                    return True
        return False

    def request(self, who, **what):
        try:
            result = who(**what).execute()
        except google.auth.exceptions.RefreshError as _:
            youtube.get_authenticated_service(refresh=True)
            result = who(**what).execute()
            log.warning("Error with request")
        return result

    def _load_next_page(self):
        pass

    def load_next_page(self):
        if self.is_loading.locked():
            return
        self.is_loading.acquire(blocking=True)
        self._load_next_page()
        self.is_loading.release()

    def update_tokens(self, response):
        self.next_page = (
            response["nextPageToken"] if "nextPageToken" in response else None
        )
        self.prev_page = (
            response["prevPageToken"] if "prevPageToken" in response else None
        )

    def get_at_index(self, index):
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""

        while index > self.nb_loaded and self.next_page != None:
            self.load_next_page()
        if self.nb_loaded == 0:
            self.load_next_page()
        if index >= self.nb_loaded:
            log.warning("index greater than size")
            return self.elements[-1]
        return self.elements[index]

    def get_item_list(self, start, end):
        while end + 1 > self.nb_loaded and self.next_page != None:
            self.load_next_page()
        max_index = min(end, self.nb_loaded)
        return self.elements[start:max_index]

    def load_all(self):
        while self.next_page != None or self.nb_loaded == 0:
            self.load_next_page()
        self.size = self.nb_loaded

    def reload(self):
        self.nb_loaded = 0
        # self.size = 0  # not necessary I think
        self.elements = []
        self.next_page = None
        self.prev_page = None

        self.load_next_page()

    def get_max_index(self):
        return self.nb_loaded - 1


class YoutubePlaylist(YoutubeList):
    def __init__(self, id, title, nb_videos):

        super().__init__()
        self.title = title
        self.id = id
        self.size = nb_videos
        self.order = [i for i in range(self.size)]  # used for playlist shuffling
        self.api_object = youtube.playlist_items

        self.load_next_page()  # we load the first page

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

    def _load_next_page(self):
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

        self.is_loading = Lock()
        super().__init__("Liked", title, 0)
        self.api_object = youtube.videos

    def is_loaded(self):
        return self.next_page is None

    def load_all(self):
        super().load_all()
        self.order = [i for i in range(self.size)]
        if self.shuffled:
            self.shuffle()

    def _load_next_page(self):
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

        idList = []
        for v in response["items"]:
            idList.append((v["id"], ""))
        nb_loaded = self._add_videos(idList)

        self.size += nb_loaded
        self.nb_loaded += nb_loaded
        self.update_tokens(response)

    def next(self):
        self.current_index += 1
        while self.current_index >= self.size and self.is_loaded():
            self.load_next_page()
        if self.current_index >= self.size and self.is_loaded():
            return Playable()
        shuffled_index = self.order[self.current_index]
        return self.get_at_index(shuffled_index)

    def shuffle(self):
        self.load_all()
        YoutubePlaylist.shuffle(self)

    def get_max_index(self):
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

        self.load_next_page()
        self.load_all()

        # we just load fully the liked videos playlist
        loader_liked = Thread(target=self.elements[0].load_all, daemon=True)
        loader_liked.start()

    def _load_next_page(self):
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

        for p in response["items"]:
            self.elements.append(
                YoutubePlaylist(
                    p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"]
                )
            )
        self.update_tokens(response)
        self.nb_loaded += len(response["items"])
        if self.next_page == None:
            self.size = self.nb_loaded

    def shuffle(self):
        return

    def unshuffle(self):
        return


class Search(YoutubePlaylist):
    def __init__(self, query):

        super().__init__()
        self.query = query
        self.size = 1e99
        self.api_object = youtube.search

        self.load_next_page()

    def _load_next_page(self):

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

        if self.next_page == None:
            self.size = self.nb_loaded

    def shuffle(self):
        return

    def unshuffle(self):
        return
