"""Youtube API wrapper"""
# === Google API === #
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import os
import pickle
import logging

import socket

log = logging.getLogger(__name__)


class YoutubeAPIObject:
    def __init__(self, element=None):
        self.element = element

    def list(self, **args):
        if self.element:
            return self.element().list(**args)
        else:
            return None

    def insert(self, **args):
        if self.element:
            return self.element().insert(**args)
        else:
            return None

    def delete(self, **args):
        if self.element:
            return self.element().delete(**args)
        else:
            return None

    def rate(self, **args):
        if self.element:
            return self.element().rate(**args)
        else:
            return None

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


def is_connected():
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        REMOTE_SERVER = "one.one.one.one"
        host = socket.gethostbyname(REMOTE_SERVER)
        # connect to the host -- tells us if the host is actually reachable
        s = socket.create_connection((host, 80), timeout=2)
        s.close()
        return True
    except Exception:
        pass  # we ignore any errors, returning False
    return False


class Youtube:
    def __init__(self):

        self.youtube = None
        self.search = YoutubeSearchAPI(self.youtube)
        self.videos = YoutubeVideoAPI(self.youtube)
        self.playlists = YoutubePlaylistAPI(self.youtube)
        self.playlist_items = YoutubePlaylistItemAPI(self.youtube)
        if is_connected():
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

        log.info("Successfully established connection to Youtube")
