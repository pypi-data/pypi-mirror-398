from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Actor:
    """
    Represents an actor in a movie.

    Attributes:
        name (Optional[str]): The name of the actor.
        voice (Optional[bool]): Indicates if the actor provided a voice-over for the movie.
        _catchall (Dict[str, str]): A catch-all dictionary for any additional attributes.
    """
    name: Optional[str] = None
    voice: Optional[bool] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Director:
    """
    Represents a movie director.

    Attributes:
        name (Optional[str]): The name of the director.
        id (Optional[str]): The ID of the director.
        _catchall (Dict[str, str]): A catch-all dictionary for any additional attributes.
    """
    name: Optional[str] = None
    id: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Posters:
    """
    Represents the posters of a movie.

    Attributes:
        thumb (Optional[str]): The URL of the thumbnail-sized poster.
        small (Optional[str]): The URL of the small-sized poster.
        regular (Optional[str]): The URL of the regular-sized poster.
        large (Optional[str]): The URL of the large-sized poster.
        _catchall (Dict[str, str]): A catch-all dictionary for any additional poster URLs.
    """
    thumb: Optional[str] = None
    small: Optional[str] = None
    regular: Optional[str] = None
    large: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MovieMeterMovie:
    """
    Represents a movie from MovieMeter.

    Attributes:
        id (Optional[int]): The ID of the movie.
        objectID (Optional[int]): The object ID of the movie.
        url (Optional[str]): The URL of the movie.
        year (Optional[int]): The year of the movie.
        imdb (Optional[str]): The IMDb ID of the movie.
        title (Optional[str]): The title of the movie.
        display_title (Optional[str]): The display title of the movie.
        alternative_title (Optional[str]): The alternative title of the movie.
        plot (Optional[str]): The plot of the movie.
        duration (Optional[int]): The duration of the movie.
        votes_count (Optional[int]): The count of votes for the movie.
        average (Optional[float]): The average rating of the movie.
        average_x2 (Optional[float]): The average rating multiplied by 2.
        average_x10 (Optional[float]): The average rating multiplied by 10.
        posters (Optional[Posters]): The posters of the movie.
        countries (Optional[List[str]]): The countries of the movie.
        genres (Optional[List[str]]): The genres of the movie.
        type (Optional[List[str]]): The type of the movie.
        actors (Optional[List[Actor]]): The actors in the movie.
        directors (Optional[List[Director]]): The directors of the movie.
        user_vote (Optional[str]): The user's vote for the movie.
        _catchall (Dict[str, str]): A catch-all dictionary for additional attributes.
    """

    id: Optional[int] = None
    objectID: Optional[int] = None
    url: Optional[str] = None
    year: Optional[int] = None
    imdb: Optional[str] = None
    title: Optional[str] = None
    display_title: Optional[str] = None
    alternative_title: Optional[str] = None
    plot: Optional[str] = None
    duration: Optional[int] = None
    votes_count: Optional[int] = None
    average: Optional[float] = None
    average_x2: Optional[float] = None
    average_x10: Optional[float] = None
    posters: Optional[Posters] = None
    countries: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    type: Optional[List[str]] = None
    actors: Optional[List[Actor]] = None
    directors: Optional[List[Director]] = None
    user_vote: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.actors = [Actor(**actor) if isinstance(actor, dict) else actor for actor in self.actors]
        self.directors = [Director(**director) if isinstance(director, dict) else director for director in self.directors]
        self.posters = Posters(**self.posters) if isinstance(self.posters, dict) else self.posters
