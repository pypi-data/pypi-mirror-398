from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.providers.tmdb.tmdb import search_movie_by_imdb, search_show_by_imdb, get_all_seasons_by_imdb_id
from datetime import datetime

class AutoTmdbMovie(AutoMovie):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'tmdb')
        self._movie = search_movie_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> int:
        return self._movie.id
    
    @property
    def title(self) -> str:
        return self._movie.title
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._movie.release_date, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._movie.runtime
    
    @property
    def titles(self) -> list:
        return [x.title for x in self._movie.alternative_titles.titles]
    
    @property
    def summary(self) -> str:
        return self._movie.overview
    
    @property
    def language(self) -> str:
        return self._movie.original_language
