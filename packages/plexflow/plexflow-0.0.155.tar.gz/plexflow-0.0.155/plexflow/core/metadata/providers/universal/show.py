from datetime import datetime
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from plexflow.core.metadata.providers.tmdb.datatypes import TmdbShow
from plexflow.core.metadata.providers.tvdb.tv_datatypes import TvdbShow
from plexflow.core.metadata.providers.imdb.datatypes import ImdbShow
from plexflow.core.metadata.providers.plex.datatypes import PlexShowMetadata

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class UniversalShow:
    tmdb_show: TmdbShow
    tvdb_show: TvdbShow
    plex_show: PlexShowMetadata
    imdb_show: ImdbShow
    
    @property
    def is_release_date_consistent(self) -> bool:
        """
        Check if the release dates from different providers (TMDB, TVDB, and IMDb) are consistent.

        Returns:
            bool: True if the release dates are consistent, False otherwise.
        """
        tmdb_date = datetime.strptime(self.tmdb_show.first_air_date, "%Y-%m-%d")
        tvdb_date = datetime.strptime(self.tvdb_show.firstAired, "%Y-%m-%d")
        imdb_date = datetime.strptime(self.imdb_show.release_date, "%Y-%m-%d")

        return tmdb_date == tvdb_date == imdb_date
        
    @property
    def is_year_consistent(self) -> bool:
        tmdb_date = datetime.strptime(self.tmdb_show.first_air_date, "%Y-%m-%d")
        tvdb_year = self.tvdb_show.year
        plex_year = self.plex_show.year
        return tmdb_date.year == tvdb_year == plex_year

    @property
    def titles(self) -> set:
        title_set = set()
        
        title_set.add(self.tmdb_show.original_name)
        title_set.add(self.tvdb_show.name)
        title_set.update(alias.name for alias in self.tvdb_show.aliases)
        title_set.update(title.title for title in self.tmdb_show.alternative_titles.results)
        title_set.add(self.plex_show.title)
        title_set.add(self.imdb_show.title)
        
        return set(map(lambda s: s.lower().strip(), title_set))

    @property
    def imdb(self) -> str:
        """
        Gets the IMDb ID of the movie.
        
        Returns:
            str: The IMDb ID of the movie.
        """
        return self.tmdb_show.imdb_id

    @property
    def title(self) -> str:
        """
        Gets the title of the movie.
        
        Returns:
            str: The title of the movie.
        """
        return self.tvdb_show.name

    @property
    def year(self) -> int:
        return self.tvdb_show.year

    @property
    def is_released(self) -> bool:
        tmdb_date = datetime.strptime(self.tmdb_show.first_air_date, "%Y-%m-%d")
        tvdb_date = datetime.strptime(self.tvdb_show.firstAired, "%Y-%m-%d")
        imdb_date = datetime.strptime(self.imdb_show.release_date, "%Y-%m-%d")
        
        now = datetime.now()
        return tmdb_date < now or tvdb_date < now or imdb_date < now

    @property
    def days_until_release(self) -> int:
        tmdb_date = datetime.strptime(self.tmdb_show.first_air_date, "%Y-%m-%d")
        tvdb_date = datetime.strptime(self.tvdb_show.firstAired, "%Y-%m-%d")
        imdb_date = datetime.strptime(self.imdb_show.release_date, "%Y-%m-%d")
        
        now = datetime.now()
        tmdb_days = (tmdb_date - now).days
        tvdb_days = (tvdb_date - now).days
        imdb_days = (imdb_date - now).days
        
        return min(tmdb_days, tvdb_days, imdb_days)

    @property
    def rank(self) -> int:
        return self.imdb_show.rank
    
    @property
    def rating(self) -> float:
        return self.imdb_show.rating

    @property
    def votes(self) -> int:
        return self.imdb_show.votes
