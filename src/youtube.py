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


scopes = ["https://www.googleapis.com/auth/youtube"]
data_path = "data/"
client_secrets_file = data_path + "client_secret.json"
api_service_name = "youtube"
api_version = "v3"
cache_path = data_path + "cache.json"

MAX_RESULTS = 50

def get_authenticated_service():
    path = data_path + "CREDENTIALS_PICKLE_FILE"
    if os.path.exists(path):
        with open(path, "rb") as f:
            credentials = pickle.load(f)
    else:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )
        credentials = flow.run_console()
        with open(path, "wb") as f:
            pickle.dump(credentials, f)
    return googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )


youtube = get_authenticated_service()
# ================== #


# === SponsorBlock === #
import sponsorblock as sb
sponsorBlock = sb.Client()
useSponsorBlock = True
toSkip = ["sponsor", "selfpromo", "music_offtopic"]
# ==================== #


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

    def getSkipSegment(self):
        # TODO: better error handling and add possibility to timeout
        try:
            self.skipSegments = sponsorBlock.get_skip_segments(video_id = self.id, categories=toSkip)
        except (sb.errors.NotFoundException, sb.errors.ServerException) as _:
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
        # TODO: error handling
        return who(**what).execute()

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
        if index > self.size:
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


class Playlist(ListItems):
    def __init__(self, id, title, nb_videos):

        ListItems.__init__(self)

        self.title = title
        self.id = id
        self.size = nb_videos

        self.loadNextPage()  # we load the first page

        self.order = [i for i in range(self.size)]  # used for playlist shuffling

    def checkVideoAvailability(self, video):
        # this condition is maybe too strong as it excludes non-repertoriated
        return video["status"]["privacyStatus"] == "public"

    def loadNextPage(self):
        to_request = "id, snippet, status"
        response = self.request(youtube.playlistItems().list,
            part=to_request,
            playlistId=self.id,
            maxResults=MAX_RESULTS,
            pageToken=self.nextPage,
        )
        for v in response["items"]:
            # exclude video that are not available to watch (hopefully)
            if not self.checkVideoAvailability(v):  
                self.nb_loaded -= 1
                self.size -= 1
                continue
            video_id = v["snippet"]["resourceId"]["videoId"]
            playlistItemId = v["id"]
            author = v["snippet"]["videoOwnerChannelTitle"]
            self.elements.append(
                Video(
                    video_id,
                    v["snippet"]["title"],
                    v["snippet"]["description"],
                    author,
                    playlistItemId=playlistItemId,
                )
            )

        self.nb_loaded = self.nb_loaded + len(response["items"])
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

    def add(self, video):
        self.request(youtube.playlistItems().insert,
            part="snippet",
            body={
                "snippet": {
                    "playlistId": self.id,
                    "resourceId": {"kind": "youtube#video", "videoId": video.id},
                },
                "position": 0,
            },
        )

        self.reload()  # we refresh the content

    def remove(self, video):
        for v in self.elements:
            if v.id == video.id:
                playlistItemId = v.playlistItemId
                break
        self.request(youtube.playlistItems().delete, id=playlistItemId)
        self.reload()

    def __str__(self):
        return self.title


class LikedVideos(Playlist):
    def __init__(self, title):

        Playlist.__init__(self, "Liked", title, 0)

        self.loadNextPage()  # we load the first page

        self.order = [i for i in range(self.size)]  # used for playlist shuffling

    def loadNextPage(self):
        to_request = "id, snippet, status"
        response = self.request(youtube.videos().list,
            part=to_request,
            myRating="like",
            maxResults=MAX_RESULTS,
            pageToken=self.nextPage,
        )
        for v in response["items"]:
            # exclude video that are not available to watch (hopefully)
            if not self.checkVideoAvailability(v):  
                self.nb_loaded -= 1
                self.size -= 1
                continue
            video_id = v["id"]
            self.elements.append(
                Video(
                    video_id,
                    v["snippet"]["title"],
                    v["snippet"]["description"],
                    v["snippet"]["channelTitle"],
                )
            )

        self.size = self.size + len(response["items"])
        self.nb_loaded = self.nb_loaded + len(response["items"])
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
        response = self.request(youtube.playlists().list,
            part="id, snippet, contentDetails",
            maxResults=MAX_RESULTS,
            mine=True,
            pageToken=self.nextPage,
        )
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


class Search(ListItems):
    def __init__(self, query):

        ListItems.__init__(self)
        self.query = query
        self.size = 1e99

        self.loadNextPage()

    def loadNextPage(self):

        response = self.request(youtube.search().list,
            part="id, snippet",
            maxResults=MAX_RESULTS,
            pageToken=self.nextPage,
            q=self.query,
            type="video",
        )
        for v in response["items"]:
            self.elements.append(
                Video(
                    v["id"]["videoId"],
                    v["snippet"]["title"],
                    v["snippet"]["description"],
                    v["snippet"]["channelTitle"],
                )
            )
        self.updateTokens(response)
        self.nb_loaded += len(response["items"])
        if self.nextPage == None:
            self.size = self.nb_loaded
