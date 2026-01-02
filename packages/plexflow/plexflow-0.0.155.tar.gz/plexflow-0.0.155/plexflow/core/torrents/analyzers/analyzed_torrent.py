from plexflow.core.torrents.results.torrent import Torrent
from datetime import datetime
from plexflow.utils.imdb.imdb_codes import IMDbCode
from typing import List, Union
from plexflow.utils.torrent.files import TorrentFile

class AnalyzedTorrent:
    def __init__(self, torrent: Torrent, **kwargs):
        self._torrent = torrent
        self._details = kwargs
        self._ai_details = {}

    def update_from_ai(self, **kwargs):
        self._ai_details.update(kwargs)
    
    @property
    def release_name(self):
        return self._torrent.release_name or self._details.get('release_name') or self._ai_details.get('release_name')

    @property
    def seeds(self) -> int:
        return self._torrent.seeds or self._details.get('seeds') or self._ai_details.get('seeds')
    
    @property
    def peers(self) -> int:
        return self._torrent.peers or self._details.get('peers') or self._ai_details.get('peers')
        
    @property
    def size_bytes(self) -> int:
        return self._torrent.size_bytes or self._details.get('size_bytes') or self._ai_details.get('size_bytes')
    
    @property
    def magnet(self) -> str:
        return self._torrent.magnet or self._details.get('magnet')
    
    @property
    def hash(self) -> str:
        return self._torrent.hash or self._details.get('hash')
    
    @property
    def uploader(self) -> str:
        return self._torrent.uploader or self._details.get('uploader') or self._ai_details.get('uploader')
    
    @property
    def date(self) -> datetime:
        return self._torrent.date or self._details.get('date') or self._ai_details.get('date')
    
    @property
    def imdb_code(self) -> IMDbCode:
        return self._torrent.imdb_code or IMDbCode(self._details.get('imdb_code')) if self._details.get('imdb_code') else None
    
    @property
    def source(self) -> str:
        return self._torrent.source
    
    @property
    def torrent_id(self) -> str:
        return self._torrent.torrent_id or self._details.get('torrent_id')

    @property
    def parsed_release_name(self) -> dict:
        return self._torrent.parsed_release_name
    
    @property
    def encoder_name(self) -> str:
        return self._torrent.encoder_name

    @property
    def season(self) -> Union[int, List[int]]:
        return self._torrent.season
    
    @property
    def episode(self) -> Union[int, List[int]]:
        return self._torrent.episode

    @property
    def has_multiple_episodes(self):
        return self._torrent.has_multiple_episodes

    @property
    def has_multiple_seasons(self):
        return self._torrent.has_multiple_seasons
        
    @property
    def title(self) -> str:
        return self._torrent.title
        
    @property
    def year(self) -> int:
        return self._torrent.year

    @property
    def quality(self) -> str:
        return self._torrent.quality

    @property
    def is_bad_quality(self):
        return self._torrent.is_bad_quality

    @property
    def url(self) -> str:
        return self._torrent.url
    
    @property
    def html_content(self) -> str:
        return self._details.get('html_content')

    @property
    def resolved_urls(self) -> dict:
        return self._details.get('resolved_urls')

    @property
    def files(self) -> List[TorrentFile]:
        return self._details.get('file_list')
    
    @property
    def has_native_subtitles(self):
        subs = self._details.get('subtitles')
        if subs and len(subs) > 0:
            return True
        return False
    
    @property
    def has_native_dutch_subtitles(self):
        subs = self._details.get('subtitles')
        if subs and len(subs) > 0:
            for sub in subs:
                if 'dutch' in sub.lower():
                    return True
        return False
    
    @property
    def has_native_english_subtitles(self):
        subs = self._details.get('subtitles')
        if subs and len(subs) > 0:
            for sub in subs:
                if 'english' in sub.lower():
                    return True
        return False
    
    @property
    def native_subtitles(self):
        return self._details.get('subtitles')