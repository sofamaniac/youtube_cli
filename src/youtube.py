# -*- coding: utf-8 -*-
import os
import pickle
import subprocess
import shlex
from random import shuffle

# === Google API === #
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.exceptions


scopes = ["https://www.googleapis.com/auth/youtube"]
data_path = "data/"
client_secrets_file = data_path + "client_secret.json"
api_service_name = "youtube"
api_version = "v3"
cache_path = data_path + "cache.json"

MAX_RESULTS = 50
youtube = None

def get_authenticated_service(refresh=False):
    global youtube
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
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )

get_authenticated_service()

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

class TimeoutException(Exception): pass

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

class Video:
    def __init__(self, id="", title="", description="", author="", playlistItemId=""):
        self.title = title
        self.id = id
        self.description = description
        self.author = author
        self.playlistItemId = playlistItemId  # useful for editing playlist
        self.skipSegments = []

    def getUrl(self, video=False):
        """Return the url for the audio stream of the video"""

        if video:
            format = "best"
        else:
            format = "bestaudio/best"

        sort = ""  # sort to be applied to the results

        command = f"yt-dlp --no-warnings --format {format} {sort} --print urls --no-playlist https://youtu.be/{self.id}"
        urls = subprocess.run(shlex.split(command), capture_output=True, text=True)
        urls = urls.stdout.splitlines()
        if urls:
            if useSponsorBlock:
                self.getSkipSegment()
            return urls[0]
        else:
            return ""

    def __getSkipSegment(self):
        try:
            skipSegments = sponsorBlock.get_skip_segments(video_id=self.id, categories=toSkip)
        except (sb.errors.NotFoundException, sb.errors.ServerException, sb.errors.ServerException) as _:
            skipSegments = []
        finally:
            queue.put(skipSegments)

    def getSkipSegment(self):
        try:
            self.skipSegments = run_with_limited_time(self.__getSkipSegment, (), {}, sponsorBlockTimeout)
        except (TimeoutException) as _:
            self.skipSegments = []

    def checkSkip(self, time):
        for skip in self.skipSegments:
            if skip.start <= time <= skip.end:
                return skip.end
        return False
    
    def __str__(self):
        return self.title


class ListItems:
    def __init__(self):
        self.currentIndex = 0
        self.nextPage = None
        self.prevPage = None

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
        last_index = len(self.elements)-1
        while self.nextPage != None:
            self.loadNextPage()
            for v in self.elements[last_index:]:
                last_index += 1
                if v.id == item:
                    return True
        return False
    
    def request(self, who, **what):
        try:
            result = who(**what).execute()
        except google.auth.exceptions.RefreshError as _:
            get_authenticated_service(refresh=True)
            result = who(**what).execute()
        return result


    def loadNextPage(self):
        pass

    def updateTokens(self, response):
        self.nextPage = (
            response["nextPageToken"] if "nextPageToken" in response else None
        )
        self.prevPage = (
            response["prevPageToken"] if "prevPageToken" in response else None
        )

    def getCurrent(self):
        return self.elements[self.currentIndex]

    def getAtIndex(self, index):
        """If the index is greater than the number of elements in the list,
        does NOT raise an error but return the last element of the list instead"""

        while index > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()
        if index >= self.nb_loaded:
            return self.elements[-1]
        return self.elements[index]

    def getItemList(self, start, end):
        while end + 1 > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()
        max_index = min(end, self.nb_loaded)
        return self.elements[start:max_index]

    def loadAll(self):
        while self.nextPage != None or self.nb_loaded == 0:
            self.loadNextPage()
        self.size = self.nb_loaded

    def reload(self):
        self.nb_loaded = 0
        self.size = 0
        self.elements = []
        self.nextPage = None
        self.prevPage = None

        self.loadNextPage()

    def getMaxIndex(self):
        return self.nb_loaded - 1

    def shuffle(self):
        pass

    def unshuffle(self):
        pass


class Playlist(ListItems):
    def __init__(self, id, title, nb_videos):

        ListItems.__init__(self)

        self.title = title
        self.id = id
        self.size = nb_videos

        self.loadNextPage()  # we load the first page

        self.order = [i for i in range(self.size)]  # used for playlist shuffling

    def _addVideos(self, idList):

        to_request = "id, snippet, status, contentDetails"
        args = { "part": to_request,
                 "id": ','.join(idList),
                 }
        response = self.request(youtube.videos().list, **args)
        
        nb_added = 0
        for v in response["items"]:
            if not self.checkVideoAvailability(v):
                self.size -= 1
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

    def checkVideoAvailability(self, video):
        # this condition is maybe too strong as it excludes non-repertoriated
        result = video["status"]["privacyStatus"] == "public"
        if "regionRestriction" in video["contentDetails"]:
            t = video["contentDetails"]["regionRestriction"]
            if "blocked" in t:
                result = result and "FR" not in t["blocked"]
            else:
                result = result and "FR" in t["allowed"]
        return result

    def loadNextPage(self):
        to_request = "id, snippet, status, contentDetails"
        args = { "part": to_request,
                "playlistId": self.id,
                "maxResults": MAX_RESULTS,
                "pageToken": self.nextPage,
                }
        response = self.request(youtube.playlistItems().list, **args)

        idList = []
        for v in response["items"]:
            idList.append(v["snippet"]["resourceId"]["videoId"])
        self.nb_loaded += self._addVideos(idList)
        self.updateTokens(response)

    def getVideoUrl(self, index):
        return self.getAtIndex(index).getUrl()

    def shuffle(self):
        self.order = [i for i in range(self.size)]
        shuffle(self.order)

    def unshuffle(self):
        self.order = [i for i in range(self.size)]

    def next(self):
        if self.currentIndex >= self.size:
            return
        self.currentIndex += 1
        shuffled_index = self.order[self.currentIndex]
        return self.getAtIndex(shuffled_index)

    def prev(self):
        if self.currentIndex == 0:
            return
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

    def add(self, video):
        args = { "part": "snippet",
                "body": {
                    "snippet": {
                        "playlistId": self.id,
                        "resourceId": {"kind": "youtube#video", "videoId": video.id},
                    },
                    "position": 0,
                },
        }
        self.request(youtube.playlistItems().insert,**args)
        self.reload()  # we refresh the content

    def remove(self, video):
        for v in self.elements:
            if v.id == video.id:
                playlistItemId = v.playlistItemId
                break
        self.request(youtube.playlistItems().delete, id=playlistItemId)
        self.reload()
    
    def removeMax(self):
        index_max = max(range(len(self.order)), key=self.order.__getitem__)
        if self.order[index_max] >= self.size:
            self.order.pop(index_max)
            self.removeMax()  # Hopefully it will never go deep

    def __str__(self):
        return self.title


class LikedVideos(Playlist):
    def __init__(self, title):

        Playlist.__init__(self, "Liked", title, 0)

        self.loadNextPage()  # we load the first page

        self.order = [i for i in range(self.size)]  # used for playlist shuffling

    def loadNextPage(self):
        to_request = "id, snippet, status, contentDetails"
        args = { "part": to_request,
                "myRating": "like",
                "maxResults": MAX_RESULTS,
                "pageToken": self.nextPage,
                }
        response = self.request(youtube.videos().list, **args)

        idList = []
        for v in response["items"]:
            idList.append(v["id"])
        nb_loaded = self._addVideos(idList)

        self.size += nb_loaded
        self.nb_loaded += nb_loaded
        self.updateTokens(response)

    def shuffle(self):
        self.loadAll()
        Playlist.shuffle(self)

    def getMaxIndex(self):
        if self.nextPage != None:
            return 1e99
        else:
            return self.size - 1

    def add(self, video):
        self.request(youtube.Videos.rate, id=video.id, rating="like")
        self.reload()  # we refresh the content

    def remove(self, video):
        self.request(youtube.Videos.rate, id=video.id, rating="none")
        self.reload()  # we refresh the content


class PlaylistList(ListItems):
    def __init__(self):
        ListItems.__init__(self)
        self.elements = [LikedVideos("Liked Videos")]
        self.nb_loaded = 1

        self.loadNextPage()
        self.loadAll()

    def loadNextPage(self):
        args = {"part": "id, snippet, contentDetails",
                "maxResults": MAX_RESULTS,
                "mine": True,
                "pageToken": self.nextPage,
                }
        response = self.request(youtube.playlists().list, **args)

        for p in response["items"]:
            self.elements.append(
                Playlist(
                    p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"]
                )
            )
        self.updateTokens(response)
        self.nb_loaded += len(response["items"])
        if self.nextPage == None:
            self.size = self.nb_loaded


class Search(Playlist):
    def __init__(self, query):

        ListItems.__init__(self)
        self.query = query
        self.size = 1e99

        self.loadNextPage()

    def loadNextPage(self):

        args = {"part": "id, snippet, contentDetails",
                "maxResults": MAX_RESULTS,
                "pageToken": self.nextPage,
                "q": self.query,
                "type": "video",
                }

        response = self.request(youtube.search().list, **args)
        idList = []
        for v in response["items"]:
            idList.append(v["id"]["videoId"])

        self.nb_loaded += self._addVideos(idList)
        self.updateTokens(response)

        if self.nextPage == None:
            self.size = self.nb_loaded
