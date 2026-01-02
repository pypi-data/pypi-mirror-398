from plexflow.utils.api.rest.antibot_restful import AntibotRestful
from plexflow.core.torrents.providers.torrentquest.utils import TorrentQuestSearchResult
from plexflow.utils.torrent.extract.torrentquest import extract_torrent_results
from typing import List
import os

class TorrentQuest(AntibotRestful):
    def __init__(self, base_url: str = 'https://torrentquest.com', use_xvfb: bool = os.getenv('USE_XVFB', 'false').lower() == 'true'):
        super().__init__(base_url=base_url, use_xvfb=use_xvfb)
    
    def search(self, query: str) -> List[TorrentQuestSearchResult]:
        capture = self.get('/search', query_params={
            'q': query,
            'm': '1',
            'x': '14',
            'y': '17',
        }, wait_condition='regex', wait_value='Download Name')
        
        data = extract_torrent_results(html=capture.html)
        return list(map(lambda t: TorrentQuestSearchResult(**t), data))
