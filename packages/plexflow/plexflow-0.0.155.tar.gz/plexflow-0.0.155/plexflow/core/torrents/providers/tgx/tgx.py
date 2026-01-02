from plexflow.utils.api.rest.restful import Restful
from plexflow.core.torrents.providers.tgx.utils import TGXSearchResult

class TGX(Restful):
    def __init__(self, postgres_conn_id: str = 'postgresql_hook', config_folder: str = 'config'):
        super().__init__(postgres_conn_id=postgres_conn_id, config_folder=config_folder)
    
    def search(self, imdb: str):
        rows = self.get_all("""
                        SELECT 
                            * 
                        FROM tgx.results 
                        WHERE 
                            imdb = %(imdb)s 
                        AND
                            category IN ('movies', 'tv')
                        LIMIT 1000
                     """, params={
                         "imdb": imdb, 
                     })
                
        return list(map(lambda x: TGXSearchResult(**x), rows))
