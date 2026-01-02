from plexflow.core.torrents.providers.tpb.tpb import TPB
from plexflow.core.torrents.providers.yts.yts import YTS
from plexflow.core.torrents.providers.torrentquest.torrentquest import TorrentQuest
from plexflow.core.torrents.providers.extratorrent.extratorrent import ExtraTorrent
from plexflow.core.torrents.providers.ext.ext import Ext
from plexflow.core.torrents.providers.snowfl.snowfl import Snowfl
from plexflow.core.torrents.providers.therarbg.therarbg import TheRarbg
from plexflow.core.torrents.providers.piratesparadise.piratesparadise import PiratesParadise

from typing import List
from plexflow.core.torrents.results.torrent import Torrent

class AutoTorrents:
    @staticmethod
    def movie(imdb_id: str = None, query: str = None, source: str = 'yts', headless: bool = True, **kwargs) -> List[Torrent]:
        if source == 'tpb':
            return TPB(**kwargs).search(query=imdb_id, headless=headless, **kwargs)
        elif source == 'yts':
            return YTS().search(query=imdb_id, headless=headless, **kwargs)
        elif source == 'torrentquest':
            return TorrentQuest(**kwargs).search(query=query)
        elif source == 'extratorrent':
            return ExtraTorrent(**kwargs).search(query=query)
        elif source == 'therarbg':
            return TheRarbg(**kwargs).search(query=imdb_id, headless=headless, **kwargs)
        elif source == 'ext':
            return Ext(**kwargs).search(query=query)
        elif source == 'snowfl':
            return Snowfl(**kwargs).search(query=query)
        elif source == "piratesparadise":
            return PiratesParadise().search(query=query, kwargs=kwargs)
        else:
            raise ValueError(f"Invalid source: {source}")

    @staticmethod
    def show(imdb_id: str = None, query: str = None, source: str = 'tpb', headless: bool = True, **kwargs) -> List[Torrent]:
        if source == 'tpb':
            return TPB(**kwargs).search(query=imdb_id if not query else query, headless=headless, **kwargs)
        elif source == 'torrentquest':
            return TorrentQuest(**kwargs).search(query=query)
        elif source == 'extratorrent':
            return ExtraTorrent(**kwargs).search(query=query)
        elif source == 'therarbg':
            return TheRarbg(**kwargs).search(query=imdb_id, headless=headless, **kwargs)
        elif source == 'ext':
            return Ext(**kwargs).search(query=query)
        elif source == 'snowfl':
            return Snowfl(**kwargs).search(query=query)
        elif source == "piratesparadise":
            return PiratesParadise().search(query=query, kwargs=kwargs)
        else:
            raise ValueError(f"Invalid source: {source}")
