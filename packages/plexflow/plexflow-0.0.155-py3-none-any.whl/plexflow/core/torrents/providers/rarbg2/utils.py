from datetime import datetime
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode

class RARBG2SearchResult(Torrent):
    id: str
    name: str
    info_hash: str
    leechers: str
    seeders: str
    num_files: str
    size: str
    username: str
    added: str
    status: str
    category: str
    imdb: str
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.info_hash = kwargs.get("info_hash")
        self.leechers = kwargs.get("leechers")
        self.seeders = kwargs.get("seeders")
        self.num_files = kwargs.get("num_files")
        self.size = kwargs.get("size")
        self.username = kwargs.get("username")
        self.added = kwargs.get("added")
        self.status = kwargs.get("status")
        self.category = kwargs.get("category")
        self.imdb = kwargs.get("imdb")
        self.src = "rarbg2"

    @property
    def magnet(self) -> str:
        return f'magnet:?xt=urn:btih:{self.info_hash}'

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(int(self.added))

    @property
    def seeds(self) -> int:
        return int(self.seeders)

    @property
    def peers(self) -> int:
        return int(self.leechers)

    @property
    def n_files(self) -> int:
        return int(self.num_files)

    @property
    def size_bytes(self) -> int:
        return int(self.size)

    @property
    def imdb_code(self) -> IMDbCode:
        return IMDbCode(self.imdb)

    @property
    def hash(self) -> str:
        return self.info_hash
    
    @property
    def release_name(self) -> str:
        return self.name

    @property
    def uploader(self) -> str:
        return self.username

    @property
    def torrent_id(self) -> str:
        return self.id
