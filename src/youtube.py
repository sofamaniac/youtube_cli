# -*- coding: utf-8 -*-
import os
import pickle
import subprocess
import shlex
from random import shuffle
from playlist import *

# === Google API === #
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.exceptions


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
            YoutubeAPIObject.__init__(self, youtube.videos)
        else:
            YoutubeAPIObject.__init__(self, None)

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.videos)


class YoutubePlaylistItemAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            YoutubeAPIObject.__init__(self, youtube.playlistItems)
        else:
            YoutubeAPIObject.__init__(self, None)

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.playlistItems)


class YoutubePlaylistAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            YoutubeAPIObject.__init__(self, youtube.playlists)
        else:
            YoutubeAPIObject.__init__(self, None)

    def update(self, youtube):
        YoutubeAPIObject.update(self, youtube.playlists)


class YoutubeSearchAPI(YoutubeAPIObject):
    def __init__(self, youtube):
        if youtube:
            YoutubeAPIObject.__init__(self, youtube.search)
        else:
            YoutubeAPIObject.__init__(self, None)

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

sponsorBlock = sb.Client()
useSponsorBlock = True
sponsorBlockTimeout = 5  # timeout in seconds
toSkip = ["sponsor", "selfpromo", "music_offtopic"]
# ==================== #

# === Timeout on functions === #
# code found at https://stackoverflow.com/a/26664130
from multiprocessing import Process, Queue

queue = Queue()


class TimeoutException(Exception):
    pass


def run_with_limited_time(func, args, kwargs, time):
    """Runs a function with time limit

    :param func: The function to run
    :param args: The functions args, given as tuple
    :param kwargs: The functions keywords, given as dict
    :param time: The time limit in seconds
    :return: True if the function ended successfully. False if it was terminated.
    """

    # First we ensure the queue we are using is empty
    while not queue.empty():
        queue.get()
    p = Process(target=func, args=args, kwargs=kwargs)
    p.start()
    p.join(time)
    if p.is_alive():
        p.terminate()
        raise TimeoutException
    else:
        result = queue.get()
        return result


# ============================= #


class Video(Playable):
    def __init__(self, id="", title="", description="", author="", playlistItemId=""):
        Playable.__init__(self, title, author, id)
        self.description = description
        self.playlistItemId = playlistItemId  # useful for editing playlist
        self.skipSegments = []
        self.skipSegmentsDone = False
        self.url = ""

    def fetch_url(self, video=False):
        self.url = self.get_url(video)

    def get_url(self, video=False, refresh=False):
        """Return the url for the audio stream of the video"""

        if self.url and not refresh:
            return self.url

        if video:
            format = "best"
        else:
            format = "bestaudio/best"

        sort = ""  # sort to be applied to the results

        command = f"yt-dlp --no-warnings --format {format} {sort} --print urls --no-playlist https://youtu.be/{self.id}"
        urls = subprocess.run(shlex.split(command), capture_output=True, text=True)
        urls = urls.stdout.splitlines()
        if urls:
            if useSponsorBlock and not self.skipSegmentsDone:
                self.get_skip_segment()
            return urls[0]
        else:
            return ""

    def __get_skip_segment(self):
        try:
            skipSegments = sponsorBlock.get_skip_segments(
                video_id=self.id, categories=toSkip
            )
        except (
            sb.errors.NotFoundException,
            sb.errors.ServerException,
            sb.errors.ServerException,
        ) as _:
            skipSegments = []
        finally:
            queue.put(skipSegments)

    def get_skip_segment(self):
        try:
            self.skipSegmentsDone = True
            self.skipSegments = run_with_limited_time(
                self.__get_skip_segment, (), {}, sponsorBlockTimeout
            )
        except (TimeoutException) as _:
            self.skipSegments = []

    def check_skip(self, time):
        for skip in self.skipSegments:
            if skip.start <= time <= skip.end:
                return skip.end
        return False


class YoutubeList(Playlist):
    def __init__(self):
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
            # TODO this error handling cannot work since the youtube object has changed, so [who] is obsolete
        return result

    def load_next_page(self):
        pass

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
        if index >= self.nb_loaded:
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
        self.size = 0
        self.elements = []
        self.next_page = None
        self.prev_page = None

        self.load_next_page()

    def get_max_index(self):
        return self.nb_loaded - 1


class YoutubePlaylist(YoutubeList):
    def __init__(self, id, title, nb_videos):

        YoutubeList.__init__(self)

        self.title = title
        self.id = id
        self.size = nb_videos
        self.order = [i for i in range(self.size)]  # used for playlist shuffling
        self.api_object = youtube.playlist_items

        self.load_next_page()  # we load the first page

    def _add_videos(self, idList):

        to_request = "id, snippet, status, contentDetails"
        args = {
            "part": to_request,
            "id": ",".join(idList),
        }
        response = self.request(youtube.videos.list, **args)

        nb_added = 0
        for v in response["items"]:
            if not self.check_video_availability(v):
                self.removeMax()
                continue
            self.elements.append(
                Video(
                    v["id"],
                    v["snippet"]["title"],
                    v["snippet"]["description"],
                    v["snippet"]["channelTitle"],
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

    def load_next_page(self):
        to_request = "id, snippet, status, contentDetails"
        args = {
            "part": to_request,
            "playlistId": self.id,
            "maxResults": MAX_RESULTS,
            "pageToken": self.next_page,
        }
        response = self.request(self.api_object.list, **args)

        idList = []
        for v in response["items"]:
            idList.append(v["snippet"]["resourceId"]["videoId"])
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
        self.request(self.api_object.insert, **args)
        self.reload()  # we refresh the content

    def remove(self, video):
        for v in self.elements:
            if v.id == video.id:
                playlistItemId = v.playlistItemId
                break
        self.request(self.api_object.delete, id=playlistItemId)
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

        YoutubePlaylist.__init__(self, "Liked", title, 0)
        self.api_object = youtube.videos

    def load_next_page(self):
        to_request = "id, snippet, status, contentDetails"
        args = {
            "part": to_request,
            "myRating": "like",
            "maxResults": MAX_RESULTS,
            "pageToken": self.next_page,
        }
        response = self.request(youtube.videos.list, **args)

        idList = []
        for v in response["items"]:
            idList.append(v["id"])
        nb_loaded = self._add_videos(idList)

        self.size += nb_loaded
        self.nb_loaded += nb_loaded
        self.update_tokens(response)

    def shuffle(self):
        self.load_all()
        YoutubePlaylist.shuffle(self)

    def get_max_index(self):
        if self.next_page != None:
            return 1e99
        else:
            return self.size - 1

    def add(self, video):
        self.request(self.api_object.rate, id=video.id, rating="like")
        self.reload()  # we refresh the content

    def remove(self, video):
        self.request(self.api_object.rate, id=video.id, rating="none")
        self.reload()  # we refresh the content


class YoutubePlaylistList(YoutubeList):
    def __init__(self):
        YoutubeList.__init__(self)
        self.elements = [LikedVideos("Liked Videos")]
        self.nb_loaded = 1
        self.api_object = youtube.playlists

        self.load_next_page()
        self.load_all()

    def load_next_page(self):
        args = {
            "part": "id, snippet, contentDetails",
            "maxResults": MAX_RESULTS,
            "mine": True,
            "pageToken": self.next_page,
        }
        response = self.request(self.api_object.list, **args)

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

        YoutubeList.__init__(self)
        self.query = query
        self.size = 1e99
        self.api_object = youtube.search

        self.load_next_page()

    def load_next_page(self):

        args = {
            "part": "id, snippet, contentDetails",
            "maxResults": MAX_RESULTS,
            "pageToken": self.next_page,
            "q": self.query,
            "type": "video",
        }

        response = self.request(self.api_object.list, **args)
        id_list = []
        for v in response["items"]:
            id_list.append(v["id"]["videoId"])

        self.nb_loaded += self._add_videos(id_list)
        self.update_tokens(response)

        if self.next_page == None:
            self.size = self.nb_loaded

    def shuffle(self):
        return

    def unshuffle(self):
        return
