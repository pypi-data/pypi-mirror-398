from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.providers.plex.plex import search_movie_by_rating_key
from datetime import datetime
from plexflow.utils.imdb.imdb_codes import extract_imdb_code

class AutoPlexMovie(AutoMovie):
    def __init__(self, rating_key: str) -> None:
        self._movie = search_movie_by_rating_key(rating_key)
        imdb_id = next((next(extract_imdb_code(g.id), None) for g in self._movie.Guid), None)
        
        super().__init__(imdb_id, 'plex')

    @property
    def id(self) -> str:
        return self._movie.ratingKey
    
    @property
    def title(self) -> str:
        return self._movie.title
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._movie.originallyAvailableAt, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._movie.duration // 60000 if isinstance(self._movie.duration, int) else None
    
    @property
    def titles(self) -> list:
        return []
    
    @property
    def summary(self) -> str:
        return self._movie.summary
    
    @property
    def language(self) -> str:
        return None
