from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason
from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode
from plexflow.core.metadata.auto.auto_providers.tvdb.episode import AutoTvdbEpisode
from plexflow.core.metadata.providers.tvdb.tvdb import get_season

class AutoTvdbSeason(AutoSeason):
    def __init__(self, parent: AutoShow, season_id: int) -> None:
        super().__init__(parent)
        self._season = get_season(season_id)

    @property
    def episodes(self) -> list[AutoEpisode]:
        return [AutoTvdbEpisode(self, x) for x in self._season.get('episodes')]
    
    @property
    def release_date(self) -> datetime:
        episodes = self._season.get('episodes')
        first_aired = next(filter(lambda x: x, map(lambda x: x.get('aired'), sorted(episodes, key=lambda x: x.get('number')))), None)
        return datetime.strptime(first_aired, '%Y-%m-%d') if first_aired else None

    @property
    def season_number(self) -> int:
        return self._season.get('number')