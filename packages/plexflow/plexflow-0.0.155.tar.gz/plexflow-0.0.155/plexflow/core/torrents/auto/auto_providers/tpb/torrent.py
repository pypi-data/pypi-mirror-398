from abc import ABC, abstractmethod
from typing import Any
from plexflow.utils.torrent.hash import extract_torrent_hash
import PTN
from plexflow.core.torrents.providers.tpb.utils import TPBSearchResult

class AutoTPBTorrent(ABC):
    def __init__(self, torrent: TPBSearchResult) -> None:
        super().__init__(imdb_id=torrent.imdb_id, release_name=torrent.title, magnet_uri=torrent.magnet_uri, source="TPB")

    @property
    @abstractmethod
    def id(self) -> Any:
        pass

    @property
    def hash(self) -> str:
        return extract_torrent_hash(self.magnet_uri)

    @property
    def release_name(self) -> str:
        return self._release_name

    @property
    def magnet_uri(self) -> str:
        return self._magnet_uri

    @property
    def parsed_release_name(self) -> dict:
        return PTN.parse(self.release_name)

    @property
    def title(self) -> str:
        return self.parsed_release_name.get("title")

    @property
    def year(self) -> int:
        return self.parsed_release_name.get("year")
    
    @property
    def encoder(self) -> str:
        return self.parsed_release_name.get("encoder")
    
    @property
    def resolution(self) -> str:
        return self.parsed_release_name.get("resolution")
    
    @property
    def quality(self) -> str:
        return self.parsed_release_name.get("quality")
    
    @property
    def is_cam(self) -> bool:
        return self.parsed_release_name.get("quality") == "CAM"

    @property
    def imdb_id(self) -> str:
        return self._imdb_id

    @property
    def source(self) -> str:
        return self._source
