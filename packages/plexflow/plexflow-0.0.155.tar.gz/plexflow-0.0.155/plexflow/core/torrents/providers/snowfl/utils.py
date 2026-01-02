from datetime import datetime
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode
import dateparser
from plexflow.utils.strings.filesize import parse_size
from plexflow.utils.torrent.hash import extract_torrent_hash

class SnowflSearchResult(Torrent):
    def __init__(self, **kwargs):
        super().__init__()
        self._url = kwargs.get("url")
        self._magnet = kwargs.get("magnet")
        self._type = kwargs.get("type")
        self._seeds = kwargs.get("seeder")
        self._peers = kwargs.get("leecher")
        self._size = kwargs.get("size")
        self._size_bytes = next(iter(parse_size(self._size)), None)
        self._age = kwargs.get("age")
        self._date = dateparser.parse(f"{self._age} ago")
        self._name = kwargs.get("name")
        self.src = "snowfl"

    @property
    def magnet(self) -> str:
        return self._magnet

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def seeds(self) -> int:
        return self._seeds

    @property
    def peers(self) -> int:
        return self._peers

    @property
    def size_bytes(self) -> int:
        return self._size_bytes

    @property
    def imdb_code(self) -> IMDbCode:
        return None

    @property
    def release_name(self) -> str:
        return self._name

    @property
    def hash(self) -> str:
        return extract_torrent_hash(self._magnet)
    
    @property
    def url(self) -> str:
        return self._url


