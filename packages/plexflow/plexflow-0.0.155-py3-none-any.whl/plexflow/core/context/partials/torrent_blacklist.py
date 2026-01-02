from plexflow.core.context.partial_context import PartialContext
from qbittorrentapi.torrents import TorrentDictionary

class TorrentBlacklist(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def ban(self, torrent: TorrentDictionary):
        hash = torrent.hash
        key = f"blacklist/torrents/{hash}"
        self.set_global(key, torrent)
    
    def is_banned(self, hash: str) -> bool:
        try:
            torrent = self.get_global(f"blacklist/torrents/{hash}")
            return isinstance(torrent, TorrentDictionary)
        except:
            return False
