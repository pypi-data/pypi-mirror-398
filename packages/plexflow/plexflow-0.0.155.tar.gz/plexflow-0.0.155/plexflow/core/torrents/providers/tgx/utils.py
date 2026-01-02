from datetime import datetime
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode

class TGXSearchResult(Torrent):
    def __init__(self, **kwargs):
        super().__init__()
        self._id = kwargs.get("id")
        self._name = kwargs.get("name")
        self._category = kwargs.get("category")
        self._sub_category = kwargs.get("sub_category")
        self._date_added = kwargs.get("date_added")
        self._uploader = kwargs.get("uploader")
        self._peers = kwargs.get("peers")
        self._seeds = kwargs.get("seeds")
        self._imdb = kwargs.get("imdb")
        self._imdb_link = kwargs.get("imdb_link")
        self._magnet = kwargs.get("magnet")
        self._hash = kwargs.get("hash")
        self._language = kwargs.get("language")
        self._subtitles = kwargs.get("subtitles")
        self._deleted = kwargs.get("deleted")
        self._errored = kwargs.get("errored")
        self._date_last_scrape = kwargs.get("date_last_scrape")
        self._size_bytes = kwargs.get("size_bytes")
        self.src = "tgx"

    @property
    def magnet(self) -> str:
        return self._magnet

    @property
    def date(self) -> datetime:
        parts = self._date_added.split(" ")
        if len(parts) > 0:
            return datetime.strptime(parts[0], "%d-%m-%Y")

    @property
    def seeds(self) -> int:
        return self._seeds

    @property
    def peers(self) -> int:
        return self._peers

    @property
    def size_bytes(self) -> int:
        return round(self._size_bytes)

    @property
    def imdb_code(self) -> IMDbCode:
        return IMDbCode(self._imdb)

    @property
    def release_name(self) -> str:
        return self._name

    @property
    def hash(self) -> str:
        return self._hash

