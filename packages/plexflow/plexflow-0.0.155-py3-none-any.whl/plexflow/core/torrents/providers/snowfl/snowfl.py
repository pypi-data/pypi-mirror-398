from plexflow.utils.api.rest.restful import Restful
from plexflow.core.torrents.providers.snowfl.utils import SnowflSearchResult
import urllib.parse

class Snowfl(Restful):
    def __init__(self, base_url: str = 'https://snowfl.com'):
        super().__init__(base_url=base_url)
    
    def search(self, query: str):
        # lets use quote_plus to encode the query
        encoded_query = urllib.parse.quote(query)
        response = self.get(
            url=f'/jZEQIcyiahCKmuKDzRzbwkSbyQHFzQnLTWnocRed/{encoded_query}/40d5GE72/1/SEED/NONE/1',
            headers={
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
            }
        )
        
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list):
            return list(map(lambda t: SnowflSearchResult(**t), data))


if __name__ == '__main__':
    snowfl = Snowfl()
    torrents = snowfl.search('Twisters 2024')
    
    print(len(torrents), "torrents found")
    
    for t in torrents:
        print(t.release_name, t.url)

