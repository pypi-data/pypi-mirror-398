from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.providers.tvdb.tvdb import search_movie_by_imdb
from datetime import datetime

class AutoTvdbMovie(AutoMovie):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'tvdb')
        self._movie = search_movie_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> int:
        return self._movie.id
    
    @property
    def title(self) -> str:
        return self._movie.name
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._movie.first_release.date, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._movie.runtime
    
    @property
    def titles(self) -> list:
        return [x.name for x in self._movie.aliases]
    
    @property
    def summary(self) -> str:
        return ""
    
    @property
    def language(self) -> str:
        return self._movie.originalLanguage
