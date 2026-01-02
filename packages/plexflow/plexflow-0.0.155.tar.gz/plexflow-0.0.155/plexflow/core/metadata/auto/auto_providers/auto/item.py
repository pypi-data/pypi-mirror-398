from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

class AutoItem(ABC):
    def __init__(self, imdb_id: str, source: str) -> None:
        self._imdb_id = imdb_id
        self._source = source
    
    @property
    @abstractmethod
    def id(self) -> Any:
        pass
    
    @property
    @abstractmethod
    def title(self) -> str:
        pass
    
    @property
    @abstractmethod
    def release_date(self) -> datetime:
        pass
    
    @property
    @abstractmethod
    def runtime(self) -> int:
        pass
    
    @property
    def year(self) -> int:
        return self.release_date.year
    
    @property
    @abstractmethod
    def titles(self) -> list:
        pass
    
    @property
    @abstractmethod
    def summary(self) -> str:
        pass
    
    @property
    @abstractmethod
    def language(self) -> str:
        pass
    
    @property
    def imdb_id(self) -> str:
        return self._imdb_id
    
    @property
    def source(self) -> str:
        return self._source