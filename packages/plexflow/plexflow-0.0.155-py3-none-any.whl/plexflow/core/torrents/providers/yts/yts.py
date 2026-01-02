from plexflow.utils.api.rest.plexful import Plexful
from plexflow.core.torrents.providers.yts.utils import YTSSearchResult

class YTS(Plexful):
    def __init__(self, base_url: str = 'https://yts.lt'):
        super().__init__(base_url=base_url)
    
    def search(self, query: str, headless: bool = True, **kwargs) -> list[YTSSearchResult]:
        if not headless and 'wait_value' not in kwargs:
            kwargs['wait_value'] = 'Query was successful'
        response = self.get(url='/api/v2/list_movies.json', query_params={
            'query_term': query,
        }, headless=headless, **kwargs)
        
        if headless:
            # print(response.content)
            
            response.raise_for_status()
            
            data = response.json()
        else:
            data = response.json
        
        data = data.get("data", {})
        movies = data.get("movies", [])
        
        results = []
        
        for m in movies:
            torrents = m.get("torrents", [])
            torrents = map(lambda t: YTSSearchResult(**{
                **t,
                "name": "_".join(filter(lambda p: p, [m.get("slug"), t.get("type"), t.get("quality"), t.get("video_codec")])) + "-YTS",
                "imdb_code": m.get("imdb_code")
                }), torrents)
            results.extend(torrents)
            
        return results
