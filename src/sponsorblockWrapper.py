"""SponsorBlock wrapper"""
# === SponsorBlock === #
import sponsorblock as sb
import jsonpickle
from property import PropertyObject

import logging

log = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


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
        self.running = False

    async def get_skip_segments(self, video_id=""):

        if not self.enableSponsorBlock:
            return []

        tmp = self.cache.query(video_id)

        if tmp:
            return tmp
        else:
            block_list = await self.run_with_timeout(video_id)
            self.cache.add_entry(video_id, block_list)
            return block_list

    async def query_servers(self, video_id=""):
        block_list = []
        try:
            block_list = self.client.get_skip_segments(
                video_id=video_id, categories=self.toSkipSponsorBlock
            )
        except (sb.errors.HTTPException,) as e:  # catches all sb-server related errors
            log.warning(f"SponsorBlock has encountered an error ({e})")
            block_list = []
        finally:
            self.block_list = block_list
            return block_list

    async def run_with_timeout(self, video_id=""):
        result = await self.query_servers(video_id)
        return result
