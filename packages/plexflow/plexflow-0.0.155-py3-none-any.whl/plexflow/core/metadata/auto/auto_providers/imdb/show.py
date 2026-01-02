from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.providers.imdb.imdb import search_show_by_imdb
from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.tmdb.season import AutoTmdbSeason, AutoSeason

class AutoImdbShow(AutoShow):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'imdb')
        self._show = search_show_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> int:
        return self._show.imdb_id
    
    @property
    def title(self) -> str:
        return self._show.title
    
    @property
    def release_date(self) -> datetime:
        return self._show.release_date
    
    @property
    def runtime(self) -> int:
        return round(self._show.runtime / 60)
   
    @property
    def titles(self) -> list:
        return []
    
    @property
    def summary(self) -> str:
        return None
    
    @property
    def language(self) -> str:
        return None

    @property
    def seasons(self) -> list[AutoSeason]:
        return []

    @property
    def total_seasons(self) -> int:
        return self._show.seasons