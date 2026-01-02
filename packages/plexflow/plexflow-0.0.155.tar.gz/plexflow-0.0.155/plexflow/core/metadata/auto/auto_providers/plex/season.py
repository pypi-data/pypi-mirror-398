from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason
from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode
from plexflow.core.metadata.providers.plex.datatypes import PlexSeasonMetadata
from plexflow.core.metadata.providers.plex.plex import search_episodes_by_season_rating_key
from plexflow.core.metadata.auto.auto_providers.plex.episode import AutoPlexEpisode

class AutoPlexSeason(AutoSeason):
    def __init__(self, parent: AutoShow, data: PlexSeasonMetadata) -> None:
        super().__init__(parent)
        self._season = data

    @property
    def episodes(self) -> list[AutoEpisode]:
        episodes = search_episodes_by_season_rating_key(key=self._season.ratingKey)
        return [AutoPlexEpisode(self, episode) for episode in episodes]
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._season.originallyAvailableAt, '%Y-%m-%d')

    @property
    def season_number(self) -> int:
        return self._season.index