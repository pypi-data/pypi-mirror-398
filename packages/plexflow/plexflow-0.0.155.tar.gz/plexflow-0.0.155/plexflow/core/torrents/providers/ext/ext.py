from plexflow.utils.api.rest.antibot_restful import AntibotRestful
from plexflow.core.torrents.providers.ext.utils import ExtSearchResult
from plexflow.utils.torrent.extract.ext import extract_torrent_results
from typing import List
import os

class Ext(AntibotRestful):
    def __init__(self, base_url: str = 'https://ext.to', use_xvfb: bool = os.getenv('USE_XVFB', 'false').lower() == 'true'):
        super().__init__(base_url=base_url, use_xvfb=use_xvfb)
    
    def search(self, query: str) -> List[ExtSearchResult]:
        capture = self.get('/search', query_params={
            'c': 'movies',
            'q': query
        })

        data = extract_torrent_results(html=capture.html)
        return list(map(lambda t: ExtSearchResult(**t), data))
