from typing import TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    from plexflow.core.metadata.auto.auto_providers.auto.season import AutoSeason

from plexflow.core.metadata.providers.imdb.imdb import search_show_by_imdb
from plexflow.core.metadata.auto.auto_providers.auto.item import AutoItem

class AutoShow(AutoItem):
    def __init__(self, imdb_id: str, source: str) -> None:
        super().__init__(imdb_id, source)
        self._imdb_info = search_show_by_imdb(self.imdb_id)
    
    @property
    def rank(self) -> int:
        return self._imdb_info.rank

    @property
    def total_seasons(self) -> int:
        return len(self.seasons)
        
    @property
    @abstractmethod
    def seasons(self) -> list['AutoSeason']:
        pass
