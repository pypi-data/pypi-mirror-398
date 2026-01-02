from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from datetime import datetime

if TYPE_CHECKING:
    from plexflow.core.metadata.auto.auto_providers.auto.episode import AutoEpisode

from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow

class AutoSeason(ABC):
    def __init__(self, parent: AutoShow) -> None:
        self._parent = parent

    @property
    def show(self) -> AutoShow:
        return self._parent

    @property
    def source(self) -> str:
        return self._parent.source
 
    @property
    def total_episodes(self) -> int:
        return len(self.episodes)
    
    @property
    @abstractmethod
    def season_number(self) -> int:
        pass
    
    @property
    @abstractmethod
    def episodes(self) -> list['AutoEpisode']:
        pass
    
    @property
    def year(self):
        return self.release_date.year
    
    @property
    @abstractmethod
    def release_date(self) -> datetime:
        pass
