from datetime import datetime
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode

class TPBSearchResult(Torrent):
    added: str
    category: str
    id: str
    imdb: str
    info_hash: str
    leechers: str
    name: str
    num_files: str
    seeders: str
    size: str
    status: str
    username: str

    def __init__(self, **kwargs):
        super().__init__()
        self.added = kwargs.get("added")
        self.category = kwargs.get("category")
        self.id = kwargs.get("id")
        self.imdb = kwargs.get("imdb")
        self.info_hash = kwargs.get("info_hash")
        self.leechers = kwargs.get("leechers")
        self.name = kwargs.get("name")
        self.num_files = kwargs.get("num_files")
        self.seeders = kwargs.get("seeders")
        self.size = kwargs.get("size")
        self.status = kwargs.get("status")
        self.username = kwargs.get("username")
        self.src = "tpb"

        self._native_dutch_subtitles = []
        self._native_english_subtitles = []

    @property
    def magnet(self) -> str:
        return rf'magnet:?xt=urn:btih:{self.info_hash}&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.bittor.pw%3A1337%2Fannounce&tr=udp%3A%2F%2Fpublic.popcorn-tracker.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.dler.org%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce'

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
    def release_name(self) -> str:
        return self.name

    @property
    def hash(self) -> str:
        return self.info_hash

    @property
    def uploader(self) -> str:
        return self.username

    @property
    def torrent_id(self) -> str:
        return self.id

    @property
    def url(self) -> str:
        return f'https://apibay.org/t.php?id={self.id}'

    @property
    def category_name(self) -> str:
        categories = {
            '100': 'Audio',
            '101': 'Music',
            '102': 'Audio books',
            '103': 'Sound clips',
            '104': 'FLAC',
            '199': 'Other',
            '200': 'Video',
            '201': 'Movies',
            '202': 'Movies DVDR',
            '203': 'Music videos',
            '204': 'Movie clips',
            '205': 'TV shows',
            '206': 'Handheld',
            '207': 'HD - Movies',
            '208': 'HD - TV shows',
            '209': '3D',
            '299': 'Other',
            '300': 'Applications',
            '301': 'Windows',
            '302': 'Mac',
            '303': 'UNIX',
            '304': 'Handheld',
            '305': 'IOS (iPad/iPhone)',
            '306': 'Android',
            '399': 'Other',
            '400': 'Games',
            '401': 'PC',
            '402': 'Mac',
            '403': 'PSx',
            '404': 'XBOX360',
            '405': 'Wii',
            '406': 'Handheld',
            '407': 'IOS (iPad/iPhone)',
            '408': 'Android',
            '499': 'Other',
            '500': 'Porn',
            '501': 'Movies',
            '502': 'Movies DVDR',
            '503': 'Pictures',
            '504': 'Games',
            '505': 'HD - Movies',
            '506': 'Movie clips',
            '599': 'Other',
            '600': 'Other',
            '601': 'E-books',
            '602': 'Comics',
            '603': 'Pictures',
            '604': 'Covers',
            '605': 'Physibles',
            '699': 'Other'
        }
        return categories.get(self.category, 'Unknown')

    