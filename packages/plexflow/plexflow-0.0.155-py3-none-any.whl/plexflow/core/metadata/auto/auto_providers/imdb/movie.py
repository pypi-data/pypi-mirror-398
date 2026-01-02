from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.providers.imdb.imdb import search_movie_by_imdb
from datetime import datetime

class AutoImdbMovie(AutoMovie):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'imdb')
        self._movie = search_movie_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> str:
        return self._movie.imdb_id
    
    @property
    def title(self) -> str:
        return self._movie.title
    
    @property
    def release_date(self) -> datetime:
        return self._movie.release_date
    
    @property
    def runtime(self) -> int:
        return round(self._movie.runtime / 60)
    
    @property
    def titles(self) -> list:
        return []
    
    @property
    def summary(self) -> str:
        return None
    
    @property
    def language(self) -> str:
        return None
