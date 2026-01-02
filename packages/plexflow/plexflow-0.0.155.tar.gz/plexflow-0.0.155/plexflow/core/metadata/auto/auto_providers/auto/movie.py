from abc import ABC, abstractmethod
from datetime import datetime
from plexflow.core.metadata.providers.imdb.imdb import search_movie_by_imdb
from plexflow.core.metadata.auto.auto_providers.auto.item import AutoItem

class AutoMovie(AutoItem):
    def __init__(self, imdb_id: str, source: str) -> None:
        super().__init__(imdb_id, source)
        self._imdb_info = search_movie_by_imdb(self.imdb_id)
    
    @property
    def rank(self) -> int:
        return self._imdb_info.rank
