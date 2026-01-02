from plexflow.utils.api.rest.antibot_restful import AntibotRestful
from plexflow.core.torrents.providers.extratorrent.utils import ExtraTorrentSearchResult
from plexflow.utils.torrent.extract.extratorrent import extract_torrent_results
from typing import List
import os

class ExtraTorrent(AntibotRestful):
    def __init__(self, base_url: str = 'https://extratorrent.st', use_xvfb: bool = os.getenv('USE_XVFB', 'false').lower() == 'true'):
        super().__init__(base_url=base_url, use_xvfb=use_xvfb)
    
    def search(self, query: str) -> List[ExtraTorrentSearchResult]:
        capture = self.get('/search', query_params={
            'search': query,
            'new': 1,
            'x': 0,
            'y': 0,
            's_cat': 1,
        })
        
        data = extract_torrent_results(html=capture.html)
        return list(map(lambda t: ExtraTorrentSearchResult(**t), data))
