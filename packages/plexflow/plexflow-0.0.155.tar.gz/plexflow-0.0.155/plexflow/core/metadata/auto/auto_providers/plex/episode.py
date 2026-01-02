from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason
from plexflow.core.metadata.providers.plex.datatypes import PlexEpisodeMetadata

class AutoPlexEpisode(AutoEpisode):
    def __init__(self, parent: AutoSeason, data: PlexEpisodeMetadata) -> None:
        super().__init__(parent=parent)
        self._episode = data
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._episode.originallyAvailableAt, '%Y-%m-%d') if self._episode.originallyAvailableAt else None

    @property
    def episode_number(self) -> int:
        return self._episode.index
    
    @property
    def title(self) -> str:
        return self._episode.title
    
    @property
    def runtime(self) -> int:
        return self._episode.duration
    
    @property
    def summary(self) -> str:
        return self._episode.summary
