from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason
from plexflow.core.metadata.providers.tmdb.tmdb import get_season_by_show_id
from plexflow.core.metadata.providers.tmdb.datatypes import SeasonEpisode

class AutoTmdbEpisode(AutoEpisode):
    def __init__(self, parent: AutoSeason, episode: SeasonEpisode) -> None:
        super().__init__(parent=parent)
        self._episode = episode
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._episode.air_date, '%Y-%m-%d') if self._episode.air_date else None

    @property
    def episode_number(self) -> int:
        return self._episode.episode_number
    
    @property
    def title(self) -> str:
        return self._episode.name
    
    @property
    def runtime(self) -> int:
        return self._episode.runtime
    
    @property
    def summary(self) -> str:
        return self._episode.overview
