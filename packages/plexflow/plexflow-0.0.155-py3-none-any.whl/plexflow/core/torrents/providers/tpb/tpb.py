from plexflow.utils.api.rest.plexful import Plexful
from plexflow.core.torrents.providers.tpb.utils import TPBSearchResult

class TPB(Plexful):
    def __init__(self, base_url: str = 'https://apibay.org'):
        super().__init__(base_url=base_url)
    
    def search(self, query: str, headless: bool = True, **kwargs) -> list[TPBSearchResult]:
        response = self.get('/q.php', query_params={
            'q': query,
        }, headless=headless, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://thepiratebay.org", # Many proxies check the origin
            "Referer": "https://thepiratebay.org/",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }, **kwargs)
        
        if headless:
            response.raise_for_status()
            data = response.json()
        else:
            data = response.json
 
        return list(map(lambda x: TPBSearchResult(**x), data))
