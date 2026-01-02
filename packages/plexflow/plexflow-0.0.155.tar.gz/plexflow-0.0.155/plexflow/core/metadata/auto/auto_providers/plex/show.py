from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason
from plexflow.core.metadata.providers.plex.plex import search_show_by_rating_key, search_seasons_by_show_rating_key
from datetime import datetime
from plexflow.utils.imdb.imdb_codes import extract_imdb_code
from plexflow.core.metadata.auto.auto_providers.plex.season import AutoPlexSeason

class AutoPlexShow(AutoShow):
    def __init__(self, rating_key: str) -> None:
        self._show = search_show_by_rating_key(rating_key)
        imdb_id = next((next(extract_imdb_code(g.id), None) for g in self._show.Guid), None)
        
        super().__init__(imdb_id, 'plex')

    @property
    def id(self) -> str:
        return self._show.ratingKey
    
    @property
    def title(self) -> str:
        return self._show.title
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._show.originallyAvailableAt, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._show.duration // 60000 if isinstance(self._show.duration, int) else None
    
    @property
    def titles(self) -> list:
        return []
    
    @property
    def summary(self) -> str:
        return self._show.summary
    
    @property
    def language(self) -> str:
        return None

    @property
    def seasons(self) -> list[AutoSeason]:
        seasons = search_seasons_by_show_rating_key(key=self.id)
        return [AutoPlexSeason(self, season) for season in seasons]