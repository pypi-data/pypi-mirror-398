from datetime import datetime
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from plexflow.core.metadata.providers.tmdb.datatypes import TmdbMovie
from plexflow.core.metadata.providers.tvdb.datatypes import TvdbMovie
from plexflow.core.metadata.providers.imdb.datatypes import ImdbMovie
from plexflow.core.metadata.providers.moviemeter.datatypes import MovieMeterMovie
from plexflow.core.metadata.providers.plex.datatypes import PlexMovieMetadata

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class UniversalMovie:
    """
    Represents a movie with data from TmdbMovie, TvdbMovie, ImdbMovie, and MovieMeterMovie.
    
    Attributes:
        tmdb_movie (TmdbMovie): The TmdbMovie object.
        tvdb_movie (TvdbMovie): The TvdbMovie object.
        imdb_movie (ImdbMovie): The ImdbMovie object.
        moviemeter_movie (MovieMeterMovie): The MovieMeterMovie object.
    """
    tmdb_movie: TmdbMovie
    tvdb_movie: TvdbMovie
    imdb_movie: ImdbMovie
    moviemeter_movie: MovieMeterMovie
    plex_movie: PlexMovieMetadata

    @property
    def is_release_date_consistent(self) -> bool:
        """
        Checks whether tmdb, tvdb, and imdb have the same release date.
        
        Returns:
            bool: True if the release dates are the same, False otherwise.
        """
        if self.tmdb_movie.release_date and self.tvdb_movie.first_release.date and self.imdb_movie.release_date:
            return self.tmdb_movie.release_date == self.tvdb_movie.first_release.date == self.imdb_movie.release_date.strftime("%Y-%m-%d")
        return False

    @property
    def is_year_consistent(self) -> bool:
        """
        Checks whether tmdb, tvdb, imdb, and moviemeter have the same release year.
        
        Returns:
            bool: True if the release years are the same, False otherwise.
        """
        if self.tmdb_movie.release_date and self.tvdb_movie.first_release.date and self.imdb_movie.release_date and self.moviemeter_movie.year:
            tmdb_year = datetime.strptime(self.tmdb_movie.release_date, "%Y-%m-%d").year
            tvdb_year = datetime.strptime(self.tvdb_movie.first_release.date, "%Y-%m-%d").year
            imdb_year = self.imdb_movie.release_date.year
            moviemeter_year = self.moviemeter_movie.year
            return tmdb_year == tvdb_year == imdb_year == moviemeter_year
        return False

    @property
    def titles(self) -> set:
        """
        Gets a set of all possible titles for the movie.
        
        Returns:
            set: A set of all possible titles for the movie in lowercase.
        """
        titles = set()
        if self.tmdb_movie.title:
            titles.add(self.tmdb_movie.title.lower())
        if self.tvdb_movie.name:
            titles.add(self.tvdb_movie.name.lower())
        if self.imdb_movie.title:
            titles.add(self.imdb_movie.title.lower())
        if self.moviemeter_movie.title:
            titles.add(self.moviemeter_movie.title.lower())
        if self.tmdb_movie.alternative_titles:
            for alt_title in self.tmdb_movie.alternative_titles.titles:
                titles.add(alt_title.title.lower())
        return titles

    @property
    def imdb(self) -> str:
        """
        Gets the IMDb ID of the movie.
        
        Returns:
            str: The IMDb ID of the movie.
        """
        return self.tmdb_movie.imdb_id

    @property
    def title(self) -> str:
        """
        Gets the title of the movie.
        
        Returns:
            str: The title of the movie.
        """
        return self.tmdb_movie.title

    @property
    def year(self) -> int:
        """
        Gets the year of the movie.
        
        Returns:
            int: The year of the movie. If the year is not available in tmdb, it uses tvdb, then imdb, then moviemeter.
        """
        if self.tmdb_movie.release_date:
            return datetime.strptime(self.tmdb_movie.release_date, "%Y-%m-%d").year
        elif self.tvdb_movie.first_release.date:
            return datetime.strptime(self.tvdb_movie.first_release.date, "%Y-%m-%d").year
        elif self.imdb_movie.release_date:
            return self.imdb_movie.release_date.year
        elif self.moviemeter_movie.year:
            return self.moviemeter_movie.year
        else:
            raise ValueError("Year is not available in tmdb, tvdb, imdb, and moviemeter.")

    @property
    def is_released(self) -> bool:
        """
        Checks whether the movie is already released.
        
        Returns:
            bool: True if the movie is already released, False otherwise. If the status is not available in tmdb, it uses tvdb, then imdb.
        """
        if not self.tmdb_movie.release_date and not self.tvdb_movie.first_release.date and not self.imdb_movie.release_date:
            raise ValueError("Status is not available in tmdb, tvdb, and imdb.")
            
        now = datetime.now()
        if self.tmdb_movie.release_date:
            tmdb_date = datetime.strptime(self.tmdb_movie.release_date, "%Y-%m-%d")
            if tmdb_date <= now:
                return True
        if self.tvdb_movie.first_release.date:
            tvdb_date = datetime.strptime(self.tvdb_movie.first_release.date, "%Y-%m-%d")
            if tvdb_date <= now:
                return True
        if self.imdb_movie.release_date:
            if self.imdb_movie.release_date <= now:
                return True
        return False

    @property
    def days_until_release(self) -> int:
        """
        Gets the number of days until release.
        
        Returns:
            int: The number of days until release. If different release dates, it uses the closest.
        """
        if self.tmdb_movie.release_date and self.tvdb_movie.first_release.date and self.imdb_movie.release_date:
            tmdb_release_date = datetime.strptime(self.tmdb_movie.release_date, "%Y-%m-%d")
            tvdb_release_date = datetime.strptime(self.tvdb_movie.first_release.date, "%Y-%m-%d")
            imdb_release_date = self.imdb_movie.release_date
            return min((tmdb_release_date - datetime.now()).days, (tvdb_release_date - datetime.now()).days, (imdb_release_date - datetime.now()).days)
        elif self.tmdb_movie.release_date:
            return (datetime.strptime(self.tmdb_movie.release_date, "%Y-%m-%d") - datetime.now()).days
        elif self.tvdb_movie.first_release.date:
            return (datetime.strptime(self.tvdb_movie.first_release.date, "%Y-%m-%d") - datetime.now()).days
        elif self.imdb_movie.release_date:
            return (self.imdb_movie.release_date - datetime.now()).days
        else:
            raise ValueError("Release date is not available in tmdb, tvdb, and imdb.")

    @property
    def rank(self) -> int:
        """
        Gets the IMDb rank of the movie.
        
        Returns:
            int: The IMDb rank of the movie.
        """
        return self.imdb_movie.rank

    @property
    def rating(self) -> float:
        """
        Gets the IMDb rating of the movie.
        
        Returns:
            float: The IMDb rating of the movie.
        """
        return self.imdb_movie.rating

    @property
    def votes(self) -> int:
        """
        Gets the IMDb votes of the movie.
        
        Returns:
            int: The IMDb votes of the movie.
        """
        return self.imdb_movie.votes
