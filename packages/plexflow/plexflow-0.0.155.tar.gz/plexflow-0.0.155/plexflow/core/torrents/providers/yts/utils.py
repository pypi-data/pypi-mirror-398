from datetime import datetime
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode

class YTSSearchResult(Torrent):
    def __init__(self, **kwargs):
        super().__init__()
        self._url = kwargs.get("url")
        self._hash = kwargs.get("hash")
        self._quality = kwargs.get("quality")
        self._type = kwargs.get("type")
        self._is_repack = kwargs.get("is_repack")
        self._video_codec = kwargs.get("video_codec")
        self._bit_depth = kwargs.get("bit_depth")
        self._audio_channels = kwargs.get("audio_channels")
        self._seeds = kwargs.get("seeds")
        self._peers = kwargs.get("peers")
        self._size = kwargs.get("size")
        self._size_bytes = kwargs.get("size_bytes")
        self._date_uploaded = kwargs.get("date_uploaded")
        self._name = kwargs.get("name")
        self._imdb_code = kwargs.get("imdb_code")
        self._date_uploaded_unix = kwargs.get("date_uploaded_unix")
        self.src = "yts"

    @property
    def magnet(self) -> str:
        return f'magnet:?xt=urn:btih:{self._hash}'

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(int(self._date_uploaded_unix))

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
        return IMDbCode(self._imdb_code)

    @property
    def release_name(self) -> str:
        return self._name

    @property
    def hash(self) -> str:
        return self._hash

