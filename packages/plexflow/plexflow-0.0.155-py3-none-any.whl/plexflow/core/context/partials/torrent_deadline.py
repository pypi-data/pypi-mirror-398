from plexflow.core.context.partial_context import PartialContext
from qbittorrentapi.torrents import TorrentDictionary
from datetime import datetime

class TorrentDeadline(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def track(self, torrent: TorrentDictionary, deadline: datetime):
        hash = torrent.hash
        key = f"deadlines/torrents/{hash}"
        self.set(key, deadline)
    
    def deadline(self, torrent: TorrentDictionary) -> datetime:
        try:
            hash = torrent.hash
            return self.get(f"deadlines/torrents/{hash}")
        except:
            return None

    def reset(self, torrent: TorrentDictionary):
        hash = torrent.hash
        self.set(f"deadlines/torrents/{hash}", None)
