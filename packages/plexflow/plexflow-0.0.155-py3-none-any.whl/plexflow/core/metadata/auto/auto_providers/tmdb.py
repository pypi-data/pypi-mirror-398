from plexflow.core.metadata.providers.tmdb.tmdb import search_movie_by_imdb, search_show_by_imdb, get_all_seasons_by_imdb_id
from datetime import datetime

class AutoTmdbMovie:
    """
    Represents a movie retrieved from the TMDb (The Movie Database) API.

    Attributes:
        imdb_id (str): The IMDb ID of the movie.

    Properties:
        title (str): The title of the movie.
        release_date (datetime): The release date of the movie.
        runtime (int): The runtime of the movie in minutes.
        year (int): The year of the movie's release.
        titles (list): A list of alternative titles for the movie.
        summary (str): The summary or overview of the movie.
        language (str): The original language of the movie.
    """

    def __init__(self, imdb_id: str) -> None:
        self.imdb_id = imdb_id
        self._movie = search_movie_by_imdb(self.imdb_id)
    
    @property
    def title(self) -> str:
        return self._movie.title
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._movie.release_date, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._movie.runtime
    
    @property
    def year(self) -> int:
        return self.release_date.year
    
    @property
    def titles(self) -> list:
        return [x.title for x in self._movie.alternative_titles]
    
    @property
    def summary(self) -> str:
        return self._movie.overview
    
    @property
    def language(self) -> str:
        return self._movie.original_language

class AutoTmdbShow:
    def __init__(self, imdb_id: str) -> None:
        self.imdb_id = imdb_id
        self._show = search_show_by_imdb(self.imdb_id)
    
    @property
    def title(self) -> str:
        return self._show.original_name
    
    @property
    def release_date(self) -> datetime:
        return datetime.strptime(self._show.first_air_date, '%Y-%m-%d')
    
    @property
    def runtime(self) -> int:
        return self._show.episode_run_time
    
    @property
    def year(self) -> int:
        return self.release_date.year
    
    @property
    def titles(self) -> list:
        return [x.title for x in self._show.alternative_titles.results]
    
    @property
    def summary(self) -> str:
        return self._show.overview
    
    @property
    def language(self) -> str:
        return self._show.original_language
    
    @property
    def total_seasons(self) -> int:
        return self._show.number_of_seasons
    
    @property
    def seasons(self) -> list:
        return get_all_seasons_by_imdb_id(self.imdb_id)