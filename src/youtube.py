# -*- coding: utf-8 -*-
import os
import pickle
# === Google API === #
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
# ================== #
import isodate
import json
import threading
import time
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

    def load(self, id:str):
        pass

    def getUrl(self):
        """Return the url for the audio stream of the video"""
        if self.id == "":
            1/0
        command = f"yt-dlp --no-warnings --format bestaudio/best --print urls --no-playlist https://youtu.be/{self.id}"
        urls = subprocess.run(shlex.split(command),
                capture_output=True, text=True)
        urls = urls.stdout.splitlines()
        if urls:
            return urls[0]
        else:
            return ""

    def loadNextPage(self):
        return

class Playlist():

    def __init__(self, id, title, nb_videos, **kwargs):

        self.title = title
        self.id = id
        self.videos = []
        self.nb_loaded = 0
        self.other = kwargs
        self.size = nb_videos
        self.nextPage = None
        self.prevPage = None
        self.order = []
        self.currentIndex = 0

        self.loadNextPage()  # we load the first page

    def loadNextPage(self):
        response = None
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
            self.videos.append(Video(video_id, v["snippet"]["title"], v["snippet"]["description"], v["snippet"]["channelTitle"]))

        # self.title = response["snippet"]["title"]
        self.size = self.size + len(response["items"]) if self.id == "Liked" else self.size
        self.nb_loaded = self.nb_loaded + len(response["items"])
        self.nextPage = response["nextPageToken"] if "nextPageToken" in response else None
        self.prevPage = response["prevPageToken"] if "prevPageToken" in response else None

    def getVideoUrl(self, index):
        while index+1 > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()

        if index > self.size:
            raise IndexError("Video index out of playlist range")
        return self.videos[index].getUrl()

    def getItemList(self, start, end):
        while end+1 > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()
        max_index = min(end, self.size)
        return self.videos[start:max_index]

    def loadAll(self):
        while self.nextPage != None or self.nb_loaded == 0:
            self.loadNextPage()

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
        return self.getVideoUrl(self.currentIndex)

    def prev(self):
        if self.currentIndex == 0:
            return
        self.currentIndex -= 1
        return self.getVideoUrl(self.currentIndex)

    def getItem(self, index):
        return self.getItemList(index, index+1)[0]

    def getMaxIndex(self):
        if self.id == "Liked" and self.nextPage != None:
            return 1e99
        else:
            return self.size - 1

class PlaylistList():

    def __init__(self):
        self.playlists = [Playlist("Liked", "Liked Videos", 0)]
        self.nb_loaded = 1
        self.prevPage = None
        self.nextPage = None

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
            self.playlists.append(Playlist(p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"]))
        self.nextPage = response["nextPageToken"] if "nextPageToken" in response else None
        self.prevPage = response["prevPageToken"] if "prevPageToken" in response else None
        self.nb_loaded += len(response["items"])

    def getItemList(self, start, end):
        while end+1 > self.nb_loaded and self.nextPage != None:
            self.loadNextPage()
        return self.playlists[start:end]

    def loadAll(self):
        while self.nextPage != None or self.nb_loaded == 0:
            self.loadNextPage()

    def getItem(self, index):
        return self.getItemList(index, index+1)[0]

    def getMaxIndex(self):
        return self.nb_loaded - 1


class YoutbeHandler(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.playlists_list = [["", "Liked Videos"]]
        self.currentContent = []
        self.to_fullfill = []
        self._terminate = False


    def run(self):
        while not self._terminate:
            while self.to_fullfill:
                r = self.to_fullfill.pop()
                r["object"].loadNextPage()
            time.sleep(1/10)

    def terminate(self):
        self._terminate = True

    def request(self, fetcher, page=None, result=[], **kwargs):
        self.to_fullfill.append({"fetch": fetcher, "page":page, "result": result, "kwargs":kwargs})


    def getSearch(self):
        pass


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
