from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.providers.moviemeter.moviemeter import search_movie_by_imdb
from datetime import datetime

class AutoMovieMeterMovie(AutoMovie):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'moviemeter')
        self._movie = search_movie_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> int:
        return self._movie.id
    
    @property
    def title(self) -> str:
        return self._movie.display_title
    
    @property
    def release_date(self) -> datetime:
        return None
    
    @property
    def runtime(self) -> int:
        return self._movie.duration
    
    @property
    def titles(self) -> list:
        return list(filter(lambda x: x, [self._movie.title, self._movie.alternative_title]))
    
    @property
    def summary(self) -> str:
        return self._movie.plot

    @property
    def year(self) -> int:
        return self._movie.year
    
    @property
    def language(self) -> str:
        return None
