from datetime import datetime
from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from typing import List, Any
from langcodes import standardize_tag

class UniversalMovie:
    def __init__(self, providers: List[AutoMovie]):
        self.providers = providers
    
    @property
    def plex_rating_key(self) -> str:
        for p in self.providers:
            if p.source == "plex":
                return p.id
        
    @property
    def title(self) -> str:
        for p in self.providers:
            if p.title:
                return p.title
    
    @property
    def year(self) -> int:
        for p in self.providers:
            if p.year:
                return p.year
    
    @property
    def rank(self) -> int:
        for p in self.providers:
            if p.rank:
                return p.rank
    
    @property
    def release_date(self) -> datetime:
        for p in self.providers:
            if p.release_date:
                return p.release_date
        
    @property
    def imdb_id(self) -> str:
        for p in self.providers:
            if p.imdb_id:
                return p.imdb_id
    
    @property
    def titles(self) -> List[str]:
        results = set()
        
        for p in self.providers:
            results.update(p.titles)
            results.add(p.title)

        return list(results)        

    @property
    def runtime(self) -> int:
        for p in self.providers:
            if p.runtime:
                return p.runtime
    
    @property
    def summary(self) -> str:
        for p in self.providers:
            if p.summary:
                return p.summary
    
    @property
    def sources(self) -> List[str]:
        return list({p.source for p in self.providers})

    @property
    def language(self) -> str:
        for p in self.providers:
            if p.language:
                return standardize_tag(p.language)

    @property
    def release_dates(self) -> List[datetime]:
        return list({p.release_date for p in self.providers if isinstance(p.release_date, datetime)})
    
    @property
    def years(self) -> List[int]:
        return list({p.year for p in self.providers if isinstance(p.year, int)})
    
    @property
    def runtimes(self) -> List[int]:
        return list({p.runtime for p in self.providers if isinstance(p.runtime, int)})
    
    @property
    def languages(self) -> List[str]:
        return list({standardize_tag(p.language) for p in self.providers if isinstance(p.language, str)})
    
    @property
    def imdb_ids(self) -> List[str]:
        return list({p.imdb_id for p in self.providers if isinstance(p.imdb_id, str)})
    
    def _is_field_consistent(self, field: str) -> bool:
        return len(getattr(self, field)) == 1
    
    @property
    def is_imdb_id_consistent(self) -> bool:
        return self._is_field_consistent("imdb_ids")
    
    @property
    def is_year_consistent(self) -> bool:
        return self._is_field_consistent("years")
    
    @property
    def is_release_date_consistent(self) -> bool:
        return self._is_field_consistent("release_dates")
    
    @property
    def is_runtime_consistent(self) -> bool:
        return self._is_field_consistent("runtimes")
    
    @property
    def is_language_consistent(self) -> bool:
        return self._is_field_consistent("languages")

    @property
    def is_released(self) -> bool:
        now = datetime.now()
        return all(d <= now for d in self.release_dates)

    @property
    def days_until_release(self) -> int:
        now = datetime.now()
        
        return min((d - now).days for d in self.release_dates)
