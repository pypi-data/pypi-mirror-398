from plexflow.utils.api.rest.plexful import Plexful
from plexflow.utils.api.rest.restful import Restful
from plexflow.core.torrents.providers.piratesparadise.utils import PiratesParadiseSearchResult
from plexflow.utils.torrent.extract.piratesparadise import extract_torrent_results
from typing import List
from plexflow.utils.strings.sanitize import remove_punctuation


class PiratesParadise(Plexful):
    def __init__(self, base_url: str = 'https://piratesparadise.org'):
        super().__init__(base_url=base_url)
    
    def search(self, query: str, headless: bool = True, **kwargs) -> List[PiratesParadiseSearchResult]:
        response = self.get('/search.php', query_params={
            'q': remove_punctuation(query),
        })
        
        response.raise_for_status()

        data = extract_torrent_results(html=response.text)
        
        return list(map(lambda t: PiratesParadiseSearchResult(**t), data))
