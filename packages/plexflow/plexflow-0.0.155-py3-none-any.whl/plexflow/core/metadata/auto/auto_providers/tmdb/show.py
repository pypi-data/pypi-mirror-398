from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.providers.tmdb.tmdb import search_show_by_imdb, get_all_seasons_by_imdb_id
from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.tmdb.season import AutoTmdbSeason, AutoSeason

class AutoTmdbShow(AutoShow):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'tmdb')
        self._show = search_show_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> int:
        return self._show.id
    
    @property
    def title(self) -> str:
        return self._show.original_name
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._show.first_air_date, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._show.last_episode_to_air.runtime if self._show.last_episode_to_air else next(iter(self._show.episode_run_time), None)
   
    @property
    def titles(self) -> list:
        return [x.title for x in self._show.alternative_titles.results]
    
    @property
    def summary(self) -> str:
        return self._show.overview
    
    @property
    def language(self) -> str:
        return self._show.original_language

    @property
    def seasons(self) -> list[AutoSeason]:
        return [AutoTmdbSeason(self, x.season_number) for x in self._show.seasons]
