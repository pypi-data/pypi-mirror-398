from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.providers.tvdb.tvdb import search_show_by_imdb
from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.tvdb.season import AutoTvdbSeason, AutoSeason

class AutoTvdbShow(AutoShow):
    def __init__(self, imdb_id: str) -> None:
        super().__init__(imdb_id, 'tvdb')
        self._show = search_show_by_imdb(self.imdb_id)
    
    @property
    def id(self) -> int:
        return self._show.id
    
    @property
    def title(self) -> str:
        return self._show.name
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._show.firstAired, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._show.averageRuntime
   
    @property
    def titles(self) -> list:
        return [x.name for x in self._show.aliases]
    
    @property
    def summary(self) -> str:
        return self._show.overview
    
    @property
    def language(self) -> str:
        return self._show.originalLanguage

    @property
    def seasons(self) -> list[AutoSeason]:
        return [AutoTvdbSeason(self, x.id) for x in self._show.seasons]
