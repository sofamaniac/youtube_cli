# -*- coding: utf-8 -*-
import os
import pickle
import isodate
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
import threading
import time
from pytube import YouTube, Playlist

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
data_path = "../data/"
client_secrets_file = data_path + "client_secret.json"
api_service_name = "youtube"
api_version = "v3"
cache_path = data_path + "cache.json"

MAX_RESULTS = 50

class YoutbeHandler(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.youtube = get_authenticated_service()
        self.playlists_list = [["", "Liked Videos"]]
        self.currentContent = []
        self.cache = {}
        self.to_fullfill = []
        self._terminate = False
        with open(cache_path, 'r') as f:
            self.cache = json.load(f)

    def checkInCache(self, playlist, etag=""):
        if playlist in self.cache and self.cache[playlist]["etag"] == etag:
            return self.cache[playlist]["data"]
        else:
            return []
    def writeToCache(self, playlist, data, etag):
        self.cache[playlist] = {"data": data, "etag":etag}
        with open(cache_path, "w") as f:
            json.dump(self.cache, f)

    def run(self):
        while not self._terminate:
            while self.to_fullfill:
                r = self.to_fullfill.pop()
                r["fetch"](page=r["page"], result=r["result"], **r["kwargs"])
            time.sleep(1/10)

    def terminate(self):
        self._terminate = True

    def request(self, fetcher, page=None, result=[], **kwargs):
        self.to_fullfill.append({"fetch": fetcher, "page":page, "result": result, "kwargs":kwargs})

    def getPlaylist(self, page=None, result=[], **kwargs):
        response = None
        page = page
        def aux():
            nonlocal result, page, response
            to_request = "id, snippet, status"
            # since liked video playlist has no id we must have a special request
            if kwargs["id"] == "Liked":
                request = self.youtube.videos().list(
                    part=to_request,
                    myRating="like",
                    maxResults=MAX_RESULTS,
                    pageToken=page,
                )
                response = request.execute()
                for v in response["items"]:
                    # exclude video that are not available to watch (hopefully)
                    if v["status"]["privacyStatus"] != "public":  # this condition is maybe too strong as it excludes non-repertoriated
                        continue
                    result.append({"id": v["id"], "content": v["snippet"]["title"], "description": v["snippet"]["description"],
                        "publishedBy": v["snippet"]["channelTitle"]})
            else:
                request = self.youtube.playlistItems().list(
                        part=to_request,
                        playlistId=kwargs["id"],
                        maxResults = MAX_RESULTS,
                        pageToken = page
                )
                response = request.execute()
                for v in response["items"]:
                    # exclude video that are not available to watch (hopefully)
                    if v["status"]["privacyStatus"] != "public":  # this condition is maybe too strong as it excludes non-repertoriated
                        continue
                    result.append({"id": v["snippet"]["resourceId"]["videoId"],"content": v["snippet"]["title"], 
                        "description": v["snippet"]["description"],
                        "publishedBy": v["snippet"]["channelTitle"],})

            _, page = YoutbeHandler.getPagesToken(response)
        aux()
        tmp = self.checkInCache(kwargs["id"], response["etag"])
        etag = response["etag"]
        if tmp:
            for e in tmp:
                result.append(e)
            return tmp
        else:
            while "nextPageToken" in response:
                aux()
            self.writeToCache(kwargs["id"], result, etag)
        return result

    def getPlaylistList(self, page=None, result=[], **kwargs):
        result.append({"id": "Liked", "content": "Liked"})
        response = None
        page = page
        def aux():
            nonlocal response, result, page
            request = self.youtube.playlists().list(
                    part = "id, snippet",
                    maxResults = MAX_RESULTS,
                    mine=True, 
                    pageToken=page
            )
            response = request.execute()
            for p in response["items"]:
                result.append({"id": p["id"], "content": p["snippet"]["title"]})
            _, page = YoutbeHandler.getPagesToken(response)
        aux()
        while "nextPageToken" in response:
            aux()
        return result

    def getSearch(self):
        pass
    
    def getPagesToken(response):
        prev = response["prevPageToken"] if "prevPageToken" in response else None
        next = response["nextPageToken"] if "nextPageToken" in response else None
        return prev, next


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

