import requests
from dataclasses import dataclass
import json
from plexflow.utils.api.rest.restful import Restful
from plexflow.core.torrents.providers.rarbg2.utils import RARBG2SearchResult

class RARBG2(Restful):
    def __init__(self, http_conn_id: str = 'rarbg2_hook', config_folder: str = 'config'):
        super().__init__(http_conn_id=http_conn_id, config_folder=config_folder)
    
    def search(self, query: str):
        # query params does not work due to odd values in q parameter
        response = self.get(f'/api.php?url=/q.php?q={query}')
        
        response.raise_for_status()
        
        data = response.json()
        
        return list(map(lambda x: RARBG2SearchResult(**x), data))
