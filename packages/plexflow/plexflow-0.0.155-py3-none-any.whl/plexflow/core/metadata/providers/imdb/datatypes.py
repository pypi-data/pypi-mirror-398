from datetime import datetime as dt
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImdbMovie:
    """
    Represents a movie from IMDb.

    Attributes:
        imdb_id (str): The IMDb ID of the movie.
        title (str): The title of the movie.
        release_date (dt): The release date of the movie.
        runtime (int): The runtime of the movie in minutes.
        rating (float): The rating of the movie.
        votes (int): The number of votes for the movie.
        rank (int): The rank of the movie.
    """
    imdb_id: str
    title: str
    release_date: dt
    runtime: int
    rating: float
    votes: int
    rank: int

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImdbShow:
    """
    Represents a TV show from IMDb.

    Attributes:
        imdb_id (str): The IMDb ID of the show.
        title (str): The title of the show.
        release_date (dt): The release date of the show.
        runtime (int): The runtime of each episode in minutes.
        rating (float): The average rating of the show.
        votes (int): The number of votes the show has received.
        rank (int): The IMDb rank of the show.
        episodes (int): The total number of episodes in the show.
        seasons (int): The total number of seasons in the show.
    """
    imdb_id: str
    title: str
    release_date: dt
    runtime: int
    rating: float
    votes: int
    rank: int
    episodes: int
    seasons: int