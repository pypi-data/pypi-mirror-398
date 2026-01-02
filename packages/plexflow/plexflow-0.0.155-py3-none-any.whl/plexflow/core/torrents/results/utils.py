from typing import List
from plexflow.core.torrents.results.torrent import Torrent
from collections import defaultdict
from plexflow.core.torrents.results.universal import UniversalTorrent

def create_universal_torrents(torrents: List[Torrent]) -> List[UniversalTorrent]:
    """
    This function creates a list of UniversalTorrents based on a given list of Torrent objects.
    It groups the Torrent objects by their hash and creates a UniversalTorrent for each group.
    """
    torrents_by_hash = defaultdict(list)
    for torrent in torrents:
        torrents_by_hash[torrent.hash].append(torrent)
    
    return [UniversalTorrent(torrents) for torrents in torrents_by_hash.values()]
