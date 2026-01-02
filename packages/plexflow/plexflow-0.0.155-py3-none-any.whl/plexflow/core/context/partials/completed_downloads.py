from plexflow.core.context.partial_context import PartialContext
from typing import List
from qbittorrentapi.torrents import TorrentDictionary

class CompletedDownloads(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def all(self) -> List[TorrentDictionary]:
        return self.get("download/completed")

    def update(self, downloads: List[TorrentDictionary]):
        if len(downloads) == 0:
            return
        self.set("download/completed", downloads)

    def torrent(self) -> TorrentDictionary:
        return self.get("download/torrent")

    @staticmethod
    def update_completed_torrent(universal_id: str, torrent: TorrentDictionary, **kwargs):
        PartialContext.update_custom(
            context_id=universal_id,
            key="download/torrent",
            value=torrent,
            **kwargs
        )
