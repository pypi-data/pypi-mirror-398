from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason
from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode
from plexflow.core.metadata.auto.auto_providers.tmdb.episode import AutoTmdbEpisode
from plexflow.core.metadata.providers.tmdb.tmdb import get_season_by_show_id

class AutoTmdbSeason(AutoSeason):
    def __init__(self, parent: AutoShow, season_number: int) -> None:
        super().__init__(parent)
        self._season = get_season_by_show_id(self._parent.id, season=season_number)

    @property
    def episodes(self) -> list[AutoEpisode]:
        return [AutoTmdbEpisode(self, x) for x in self._season.episodes]
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._season.air_date, '%Y-%m-%d')

    @property
    def season_number(self) -> int:
        return self._season.season_number