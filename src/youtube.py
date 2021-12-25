# -*- coding: utf-8 -*-
import os
import pickle
# === Google API === #
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
# ================== #
import subprocess
import shlex

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
data_path = "../data/"
client_secrets_file = data_path + "client_secret.json"
api_service_name = "youtube"
api_version = "v3"
cache_path = data_path + "cache.json"

MAX_RESULTS = 50


class Video():

    def __init__(self, id, title, description, author, **kwargs):
        self.title = title
        self.id = id
        self.description = description
        self.author = author
        self.other = kwargs

    def getUrl(self, video=False):
        """Return the url for the audio stream of the video"""
        
        if video:
            format = "best"
        else:
            format = "bestaudio/best"
        
        sort = ""  # sort to be applied to the results

        command = f"yt-dlp --no-warnings --format {format} {sort} --print urls --no-playlist https://youtu.be/{self.id}"
        urls = subprocess.run(shlex.split(command),
                capture_output=True, text=True)
        urls = urls.stdout.splitlines()
        if urls:
            return urls[0]
        else:
            return ""

class ListItems():
    def __init__(self):
        self.currentIndex = 0
        self.nextPage = None
        self.prevPage = None

        self.nb_loaded = 0
        self.elements = []
        self.size = 1e99

    def loadNextPage(self):
        pass

    def getCurrent(self):
        return self.elements[self.currentIndex]

    def getItem(self, index):
        item = self.getItemList(index, index+1)
        if item:
            return self.getItemList(index, index+1)[0]
        else:
            raise IndexError()

    def getItemList(self, start, end):
        while end+1 > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()
        max_index = min(end, self.size)
        return self.elements[start:max_index]

    def loadAll(self):
        while self.nextPage != None or self.nb_loaded == 0:
            self.loadNextPage()
        self.size = self.nb_loaded

    def getMaxIndex(self):
        return self.nb_loaded - 1

class Playlist(ListItems):

    def __init__(self, id, title, nb_videos, **kwargs):

        ListItems.__init__(self)

        self.title = title
        self.id = id
        self.other = kwargs
        self.size = nb_videos

        self.loadNextPage()  # we load the first page

        self.order = [i for i in range(self.size)]  # used for playlist shuffling

    def loadNextPage(self):
        to_request = "id, snippet, status"
        # since liked video playlist has no id we must have a special request

        request = None
        if self.id == "Liked":
            request = youtube.videos().list(
                part=to_request,
                myRating="like",
                maxResults=MAX_RESULTS,
                pageToken=self.nextPage,
            )
        else:
            request = youtube.playlistItems().list(
                    part=to_request,
                    playlistId=self.id,
                    maxResults = MAX_RESULTS,
                    pageToken = self.nextPage
            )
        response = request.execute()
        for v in response["items"]:
            # exclude video that are not available to watch (hopefully)
            if v["status"]["privacyStatus"] != "public":  # this condition is maybe too strong as it excludes non-repertoriated
                self.nb_loaded -= 1
                self.size -= 1
                continue
            if self.id == "Liked":
                video_id = v["id"]
            else:
                video_id = v["snippet"]["resourceId"]["videoId"]
            self.elements.append(Video(video_id, v["snippet"]["title"], v["snippet"]["description"], v["snippet"]["channelTitle"]))

        self.size = self.size + len(response["items"]) if self.id == "Liked" else self.size
        self.nb_loaded = self.nb_loaded + len(response["items"])
        self.nextPage = response["nextPageToken"] if "nextPageToken" in response else None
        self.prevPage = response["prevPageToken"] if "prevPageToken" in response else None


    def getVideoUrl(self, index):
        while index+1 > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()

        if index > self.size:
            raise IndexError("Video index out of playlist range")
        return self.elements[index].getUrl()

    def shuffle(self):
        if self.id == "Liked":
            self.loadAll()
        self.order = [i for i in range(self.size)]
        self.order.shuffle()

    def unshuffle(self):
        self.order = [i for i in range(self.size)]

    def next(self):
        if self.currentIndex >= self.size:
            return
        self.currentIndex += 1
        shuffled_index = self.order[self.currentIndex]
        return self.elements[shuffled_index]

    def prev(self):
        if self.currentIndex == 0:
            return
        self.currentIndex -= 1
        shuffled_index = self.order[self.currentIndex]
        return self.elements[shuffled_index]

    def getCurrent(self):
        shuffled_index = self.order[self.currentIndex]
        return self.elements[shuffled_index]

    def getMaxIndex(self):
        if self.id == "Liked" and self.nextPage != None:
            return 1e99
        else:
            return self.size - 1

class PlaylistList(ListItems):

    def __init__(self):
        ListItems.__init__(self)
        self.elements = [Playlist("Liked", "Liked Videos", 0)]
        self.nb_loaded = 1

        self.loadNextPage()
        self.loadAll()

    def loadNextPage(self):
        response = {}
        request = youtube.playlists().list(
                part = "id, snippet, contentDetails",
                maxResults = MAX_RESULTS,
                mine=True, 
                pageToken=self.nextPage
        )
        response = request.execute()
        for p in response["items"]:
            self.elements.append(Playlist(p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"]))
        self.nextPage = response["nextPageToken"] if "nextPageToken" in response else None
        self.prevPage = response["prevPageToken"] if "prevPageToken" in response else None
        self.nb_loaded += len(response["items"])
        if self.nextPage == None:
            self.size = self.nb_loaded

class Search(ListItems):

    def __init__(self, query):

        ListItems.__init__(self)
        self.query = query

        self.loadNextPage()

    def loadNextPage(self):

        request = youtube.search().list(
                part="snippet",
                maxResults = MAX_RESULTS,
                pageToken=self.nextPage,
                q=self.query,
                type="video"
        )
        response = request.execute()
        for v in response["items"]:
            self.elements.append(Video(v["id"]["videoId"], v["snippet"]["title"], v["snippet"]["description"], v["snippet"]["channelTitle"]))
        self.nextPage = response["nextPageToken"] if "nextPageToken" in response else None
        self.prevPage = response["prevPageToken"] if "prevPageToken" in response else None
        self.nb_loaded += len(response["items"])
        if self.nextPage == None:
            self.size = self.nb_loaded

def get_authenticated_service():
    path = data_path + "CREDENTIALS_PICKLE_FILE"
    if os.path.exists(path):
        with open(path, 'rb') as f:
            credentials = pickle.load(f)
    else:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()
        with open(path, 'wb') as f:
            pickle.dump(credentials, f)
    return googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

youtube = get_authenticated_service()
