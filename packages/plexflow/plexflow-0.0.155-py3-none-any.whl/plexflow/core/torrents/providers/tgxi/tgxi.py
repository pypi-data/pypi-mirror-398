from plexflow.utils.api.rest.plexful import Plexful
from plexflow.core.torrents.providers.therarbg.utils import TheRarbgSearchResult
from plexflow.utils.torrent.extract.therarbg import extract_torrent_results
from typing import List

class TheRarbg(Plexful):
    def __init__(self, base_url: str = 'https://therarbg.com'):
        super().__init__(base_url=base_url)
    
    def search(self, query: str, headless: bool = True, **kwargs) -> List[TheRarbgSearchResult]:
        response = self.get(f'/get-posts/keywords:{query}/')
        
        response.raise_for_status()
        
        data = extract_torrent_results(html=response.text if not headless else response.html)
        return list(map(lambda t: TheRarbgSearchResult(**t), data))
