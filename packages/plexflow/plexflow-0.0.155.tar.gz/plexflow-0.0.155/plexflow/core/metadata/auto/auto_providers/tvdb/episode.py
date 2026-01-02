from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason

class AutoTvdbEpisode(AutoEpisode):
    def __init__(self, parent: AutoSeason, episode: dict) -> None:
        super().__init__(parent=parent)
        self._episode = episode
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._episode.get('aired'), '%Y-%m-%d') if self._episode.get('aired') else None

    @property
    def episode_number(self) -> int:
        return self._episode.get('number')
    
    @property
    def title(self) -> str:
        return self._episode.get('name')
    
    @property
    def runtime(self) -> int:
        return self._episode.get('runtime')
    
    @property
    def summary(self) -> str:
        return self._episode.get('overview')
