from datetime import datetime
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode

class EZTVSearchResult(Torrent):
    """EZTVSearchResult class to handle the data structure returned by the EZTV API.

    This class inherits from the Torrent class and provides an interface to
    interact with the EZTV API. It provides a method to search for torrents
    using an IMDb ID.

    Attributes:
        id (str): The ID of the torrent.
        hash (str): The hash of the torrent.
        filename (str): The filename of the torrent.
        torrent_url (str): The URL of the torrent.
        magnet_url (str): The magnet URL of the torrent.
        title (str): The title of the torrent.
        imdb_id (str): The IMDb ID of the torrent.
        season (str): The season of the torrent.
        episode (str): The episode of the torrent.
        small_screenshot (str): The small screenshot of the torrent.
        large_screenshot (str): The large screenshot of the torrent.
        seeds (int): The number of seeds of the torrent.
        peers (int): The number of peers of the torrent.
        date_released_unix (int): The release date of the torrent in Unix time.
        size_bytes (int): The size of the torrent in bytes.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.id = kwargs.get("id")
        self._hash = kwargs.get("hash")
        self.filename = kwargs.get("filename")
        self.torrent_url = kwargs.get("torrent_url")
        self.magnet_url = kwargs.get("magnet_url")
        self._title = kwargs.get("title")
        self.imdb_id = kwargs.get("imdb_id")
        self._season = kwargs.get("season")
        self._episode = kwargs.get("episode")
        self.small_screenshot = kwargs.get("small_screenshot")
        self.large_screenshot = kwargs.get("large_screenshot")
        self._seeds = kwargs.get("seeds")
        self._peers = kwargs.get("peers")
        self.date_released_unix = kwargs.get("date_released_unix")
        self._size_bytes = kwargs.get("size_bytes")
        self.src = "eztv"

    @property
    def magnet(self) -> str:
        return self.magnet_url

    @property
    def hash(self) -> str:
        return self._hash
    
    @property
    def peers(self) -> str:
        return self._peers
    
    @property
    def seeds(self) -> str:
        return self._seeds
    
    @property
    def size_bytes(self) -> str:
        return int(self._size_bytes)

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.date_released_unix)

    @property
    def imdb_code(self) -> IMDbCode:
        return IMDbCode(self.imdb_id)

    @property
    def release_name(self) -> str:
        return self._title

    @property
    def torrent_id(self) -> str:
        return str(self.id)
