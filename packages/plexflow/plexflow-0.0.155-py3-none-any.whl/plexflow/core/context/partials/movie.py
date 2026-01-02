from plexflow.core.context.partial_context import PartialContext
from datetime import datetime as dt
from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.auto.auto_providers.tmdb.movie import AutoTmdbMovie
from plexflow.core.metadata.auto.auto_providers.tvdb.movie import AutoTvdbMovie
from plexflow.core.metadata.auto.auto_providers.moviemeter.movie import AutoMovieMeterMovie
from plexflow.core.metadata.auto.auto_providers.imdb.movie import AutoImdbMovie
from plexflow.core.metadata.auto.auto_providers.tmdb.show import AutoTmdbShow
from plexflow.core.metadata.auto.auto_providers.tvdb.show import AutoTvdbShow
from plexflow.core.metadata.auto.auto_providers.imdb.show import AutoImdbShow
from plexflow.core.metadata.auto.auto_providers.plex.movie import AutoPlexMovie

class Movie(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @property
    def sources(self) -> list:
        keys = self.get_keys("movie/*")
        # extract the source from the key
        return [key.split("/")[-1] for key in keys]

    def from_source(self, source: str) -> AutoMovie:
        return self.get(f"movie/{source}")

    @property
    def title(self) -> str:
        for source in self.sources:
            details = self.from_source(source)
            if details and details.title:
                return details.title
    
    @property
    def year(self) -> int:
        for source in self.sources:
            details = self.from_source(source)
            if details and details.year:
                return details.year
    
    @property
    def release_date(self) -> dt:
        for source in self.sources:
            details = self.from_source(source)
            if details and details.release_date:
                return details.release_date
    
    @property
    def rank(self) -> int:
        return self.plex.rank
    
    @property
    def released(self) -> bool:
        dates = []
        for source in self.sources:
            details = self.from_source(source)
            if details and details.release_date:
                dates.append(details.release_date)
        
        sorted_dates = sorted(dates)
        now = dt.now()
        return all([date < now for date in sorted_dates])
    
    @property
    def runtime(self) -> int:
        for source in self.sources:
            details = self.from_source(source)
            if details and details.runtime:
                return details.runtime

    @property
    def titles(self) -> set:
        titles = set()
        for source in self.sources:
            details = self.from_source(source)
            if details and details.title:
                titles.add(details.title)
                titles.update(details.titles)
        return titles

    @property
    def summary(self) -> str:
        for source in self.sources:
            details = self.from_source(source)
            if details and details.summary:
                return details.summary
    
    @property
    def language(self) -> str:
        for source in self.sources:
            details = self.from_source(source)
            if details and details.language:
                return details.language
        
    @property
    def plex(self) -> AutoPlexMovie:
        return self.from_source("plex")
        
    @property
    def tmdb(self) -> AutoTmdbMovie:
        return self.from_source("tmdb")
        
    @property
    def imdb(self) -> AutoImdbMovie:
        return self.from_source("imdb")
        
    @property
    def tvdb(self) -> AutoTvdbMovie:
        return self.from_source("tvdb")
        
    @property
    def moviemeter(self) -> AutoMovieMeterMovie:
        return self.from_source("moviemeter")
    
    def update(self, movie: AutoMovie):
        self.set(f"movie/{movie.source}", movie)
