from abc import ABC, abstractmethod
from datetime import datetime

from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason

class AutoEpisode(ABC):
    def __init__(self, parent: AutoSeason) -> None:
        self._parent = parent

    @property
    def source(self) -> str:
        return self._parent.source

    @property
    def season(self) -> AutoSeason:
        return self._parent

    @property
    @abstractmethod
    def runtime(self) -> int:
        pass

    @property
    def year(self) -> int:
        return self.release_date.year

    @property
    @abstractmethod
    def episode_number(self) -> int:
        pass
    
    @property
    def season_number(self) -> int:
        return self._parent.season_number
    
    @property
    @abstractmethod
    def summary(self) -> str:
        pass
    
    @property
    @abstractmethod
    def title(self) -> str:
        pass
    
    @property
    @abstractmethod
    def release_date(self) -> datetime:
        pass
