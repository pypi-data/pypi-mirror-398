from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json, Undefined
import json

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Genre:
    """
    Represents a genre of a movie.
    
    Attributes:
        id (int): The unique identifier of the genre.
        name (str): The name of the genre.
    """
    id: Optional[int] = None
    name: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ProductionCompany:
    """
    Represents a production company of a movie.
    
    Attributes:
        id (int): The unique identifier of the production company.
        logo_path (Optional[str]): The path to the logo of the production company.
        name (str): The name of the production company.
        origin_country (str): The country of origin of the production company.
    """
    id: Optional[int] = None
    logo_path: Optional[str] = None
    name: Optional[str] = None
    origin_country: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ProductionCountry:
    """
    Represents a production country of a movie.
    
    Attributes:
        iso_3166_1 (str): The ISO 3166-1 alpha-2 code of the country.
        name (str): The name of the country.
    """
    iso_3166_1: Optional[str] = None
    name: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SpokenLanguage:
    """
    Represents a language spoken in a movie.
    
    Attributes:
        english_name (str): The English name of the language.
        iso_639_1 (str): The ISO 639-1 code of the language.
        name (str): The name of the language in the original language.
    """
    english_name: Optional[str] = None
    iso_639_1: Optional[str] = None
    name: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AlternativeTitle:
    """
    Represents an alternative title of a movie.
    
    Attributes:
        iso_3166_1 (str): The ISO 3166-1 alpha-2 code of the country where the alternative title is used.
        title (str): The alternative title.
        type (str): The type of the alternative title.
    """
    iso_3166_1: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AlternativeTitles:
    """
    Represents a collection of alternative titles of a movie.
    
    Attributes:
        titles (List[AlternativeTitle]): The list of alternative titles.
    """
    titles: Optional[List[AlternativeTitle]] = None
    _catchall: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.titles = [AlternativeTitle(**title) if isinstance(title, dict) else title for title in self.titles]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AlternativeTitlesShow:
    """
    Represents a collection of alternative titles of a movie.
    
    Attributes:
        results (List[AlternativeTitle]): The list of alternative titles.
    """
    results: Optional[List[AlternativeTitle]] = None
    _catchall: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.results = [AlternativeTitle(**title) if isinstance(title, dict) else title for title in self.results]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TmdbMovie:
    """
    Represents a movie.
    
    Attributes:
        adult (bool): Whether the movie is for adults.
        backdrop_path (str): The path to the backdrop image of the movie.
        belongs_to_collection (Optional[str]): The collection the movie belongs to.
        budget (int): The budget of the movie.
        genres (List[Genre]): The genres of the movie.
        homepage (str): The homepage of the movie.
        id (int): The unique identifier of the movie.
        imdb_id (str): The IMDb identifier of the movie.
        original_language (str): The original language of the movie.
        original_title (str): The original title of the movie.
        overview (str): The overview of the movie.
        popularity (float): The popularity of the movie.
        poster_path (str): The path to the poster image of the movie.
        production_companies (List[ProductionCompany]): The production companies of the movie.
        production_countries (List[ProductionCountry]): The production countries of the movie.
        release_date (str): The release date of the movie.
        revenue (int): The revenue of the movie.
        runtime (int): The runtime of the movie.
        spoken_languages (List[SpokenLanguage]): The languages spoken in the movie.
        status (str): The status of the movie.
        tagline (str): The tagline of the movie.
        title (str): The title of the movie.
        video (bool): Whether the movie has a video.
        vote_average (float): The average vote of the movie.
        vote_count (int): The vote count of the movie.
        alternative_titles (AlternativeTitles): The alternative titles of the movie.
        _catchall (dict): A dictionary to catch all other fields not explicitly defined in the data class.
    """
    adult: Optional[bool] = None
    backdrop_path: Optional[str] = None
    belongs_to_collection: Optional[str] = None
    budget: Optional[int] = None
    genres: Optional[List[Genre]] = None
    homepage: Optional[str] = None
    id: Optional[int] = None
    imdb_id: Optional[str] = None
    original_language: Optional[str] = None
    original_title: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    production_companies: Optional[List[ProductionCompany]] = None
    production_countries: Optional[List[ProductionCountry]] = None
    release_date: Optional[str] = None
    revenue: Optional[int] = None
    runtime: Optional[int] = None
    spoken_languages: Optional[List[SpokenLanguage]] = None
    status: Optional[str] = None
    tagline: Optional[str] = None
    title: Optional[str] = None
    video: Optional[bool] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    alternative_titles: Optional[AlternativeTitles] = None
    _catchall: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.genres = [Genre(**genre) if isinstance(genre, dict) else genre for genre in self.genres]
        self.production_companies = [ProductionCompany(**pc) if isinstance(pc, dict) else pc for pc in self.production_companies]
        self.production_countries = [ProductionCountry(**pc) if isinstance(pc, dict) else pc for pc in self.production_countries]
        self.spoken_languages = [SpokenLanguage(**sl) if isinstance(sl, dict) else sl for sl in self.spoken_languages]
        self.alternative_titles = AlternativeTitles(**self.alternative_titles) if isinstance(self.alternative_titles, dict) else self.alternative_titles

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Creator:
    """
    Represents a creator of a TV show.
    
    Attributes:
        id (int): The unique identifier of the creator.
        credit_id (str): The credit identifier of the creator.
        name (str): The name of the creator.
        gender (int): The gender of the creator.
        profile_path (str): The path to the profile of the creator.
    """
    id: Optional[int] = None
    credit_id: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[int] = None
    profile_path: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Network:
    """
    Represents a network of a TV show.
    
    Attributes:
        id (int): The unique identifier of the network.
        logo_path (str): The path to the logo of the network.
        name (str): The name of the network.
        origin_country (str): The country of origin of the network.
    """
    id: Optional[int] = None
    logo_path: Optional[str] = None
    name: Optional[str] = None
    origin_country: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Season:
    """
    Represents a season of a TV show.
    
    Attributes:
        air_date (str): The air date of the season.
        episode_count (int): The number of episodes in the season.
        id (int): The unique identifier of the season.
        name (str): The name of the season.
        overview (str): The overview of the season.
        poster_path (str): The path to the poster of the season.
        season_number (int): The number of the season.
        vote_average (float): The average vote of the season.
    """
    air_date: Optional[str] = None
    episode_count: Optional[int] = None
    id: Optional[int] = None
    name: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    season_number: Optional[int] = None
    vote_average: Optional[float] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Episode:
    """
    Represents an episode of a TV show.
    
    Attributes:
        id (int): The unique identifier of the episode.
        name (str): The name of the episode.
        overview (str): The overview of the episode.
        vote_average (float): The average vote of the episode.
        vote_count (int): The vote count of the episode.
        air_date (str): The air date of the episode.
        episode_number (int): The number of the episode.
        episode_type (str): The type of the episode.
        production_code (str): The production code of the episode.
        runtime (int): The runtime of the episode.
        season_number (int): The number of the season.
        show_id (int): The id of the show.
        still_path (str): The path to the still of the episode.
    """
    id: Optional[int] = None
    name: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    air_date: Optional[str] = None
    episode_number: Optional[int] = None
    episode_type: Optional[str] = None
    production_code: Optional[str] = None
    runtime: Optional[int] = None
    season_number: Optional[int] = None
    show_id: Optional[int] = None
    still_path: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ExternalIds:
    """
    Represents the external IDs of a TV show.
    
    Attributes:
        imdb_id (str): The IMDb ID of the TV show.
        freebase_mid (str): The Freebase MID of the TV show.
        freebase_id (str): The Freebase ID of the TV show.
        tvdb_id (int): The TVDB ID of the TV show.
        tvrage_id (int): The TVRage ID of the TV show.
        wikidata_id (str): The Wikidata ID of the TV show.
        facebook_id (str): The Facebook ID of the TV show.
        instagram_id (str): The Instagram ID of the TV show.
        twitter_id (str): The Twitter ID of the TV show.
    """
    imdb_id: Optional[str] = None
    freebase_mid: Optional[str] = None
    freebase_id: Optional[str] = None
    tvdb_id: Optional[int] = None
    tvrage_id: Optional[int] = None
    wikidata_id: Optional[str] = None
    facebook_id: Optional[str] = None
    instagram_id: Optional[str] = None
    twitter_id: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TmdbShow:
    """
    Represents a TV show.
    
    Attributes:
        created_by (List[Creator]): The creators of the TV show.
        episode_run_time (List[int]): The runtime of the episodes of the TV show.
        first_air_date (str): The first air date of the TV show.
        in_production (bool): Whether the TV show is in production.
        languages (List[str]): The languages of the TV show.
        last_air_date (str): The last air date of the TV show.
        last_episode_to_air (Episode): The last episode to air.
        networks (List[Network]): The networks of the TV show.
        number_of_episodes (int): The number of episodes of the TV show.
        number_of_seasons (int): The number of seasons of the TV show.
        origin_country (List[str]): The countries of origin of the TV show.
        original_name (str): The original name of the TV show.
        seasons (List[Season]): The seasons of the TV show.
        type (str): The type of the TV show.
    """
    created_by: Optional[List[Creator]] = None
    episode_run_time: Optional[List[int]] = None
    first_air_date: Optional[str] = None
    in_production: Optional[bool] = None
    languages: Optional[List[str]] = None
    last_air_date: Optional[str] = None
    last_episode_to_air: Optional[Episode] = None
    networks: Optional[List[Network]] = None
    number_of_episodes: Optional[int] = None
    number_of_seasons: Optional[int] = None
    origin_country: Optional[List[str]] = None
    original_name: Optional[str] = None
    seasons: Optional[List[Season]] = None
    type: Optional[str] = None
    adult: Optional[bool] = None
    backdrop_path: Optional[str] = None
    belongs_to_collection: Optional[str] = None
    budget: Optional[int] = None
    genres: Optional[List[Genre]] = None
    homepage: Optional[str] = None
    id: Optional[int] = None
    imdb_id: Optional[str] = None
    original_language: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    production_companies: Optional[List[ProductionCompany]] = None
    production_countries: Optional[List[ProductionCountry]] = None
    spoken_languages: Optional[List[SpokenLanguage]] = None
    status: Optional[str] = None
    tagline: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    alternative_titles: Optional[AlternativeTitlesShow] = None
    external_ids: Optional[ExternalIds] = None

    def __post_init__(self):
        self.created_by = [Creator(**creator) if isinstance(creator, dict) else creator for creator in self.created_by]
        self.last_episode_to_air = Episode(**self.last_episode_to_air) if isinstance(self.last_episode_to_air, dict) else self.last_episode_to_air
        self.networks = [Network(**network) if isinstance(network, dict) else network for network in self.networks]
        self.seasons = [Season(**season) if isinstance(season, dict) else season for season in self.seasons]
        
        self.genres = [Genre(**genre) if isinstance(genre, dict) else genre for genre in self.genres]
        self.production_companies = [ProductionCompany(**pc) if isinstance(pc, dict) else pc for pc in self.production_companies]
        self.production_countries = [ProductionCountry(**pc) if isinstance(pc, dict) else pc for pc in self.production_countries]
        self.spoken_languages = [SpokenLanguage(**sl) if isinstance(sl, dict) else sl for sl in self.spoken_languages]
        self.alternative_titles = AlternativeTitlesShow(**self.alternative_titles) if isinstance(self.alternative_titles, dict) else self.alternative_titles
        self.external_ids = ExternalIds(**self.external_ids) if isinstance(self.external_ids, dict) else self.external_ids




from dataclasses import dataclass, field
from typing import List, Optional
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TmdbPerson:
    job: Optional[str] = None
    department: Optional[str] = None
    credit_id: Optional[str] = None
    adult: Optional[bool] = None
    gender: Optional[int] = None
    id: Optional[int] = None
    known_for_department: Optional[str] = None
    name: Optional[str] = None
    original_name: Optional[str] = None
    popularity: Optional[float] = None
    profile_path: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SeasonEpisode:
    air_date: Optional[str] = None
    episode_number: Optional[int] = None
    episode_type: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    overview: Optional[str] = None
    production_code: Optional[str] = None
    runtime: Optional[int] = None
    season_number: Optional[int] = None
    show_id: Optional[int] = None
    still_path: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    crew: Optional[List[TmdbPerson]] = None
    guest_stars: Optional[List[TmdbPerson]] = None

    def __post_init__(self):
        self.crew = [TmdbPerson(**creator) if isinstance(creator, dict) else creator for creator in self.crew]
        self.guest_stars = [TmdbPerson(**creator) if isinstance(creator, dict) else creator for creator in self.guest_stars]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Network:
    name: Optional[str] = None
    id: Optional[int] = None
    logo_path: Optional[str] = None
    origin_country: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TmdbSeason:
    air_date: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    season_number: Optional[int] = None
    vote_average: Optional[float] = None
    episodes: Optional[List[SeasonEpisode]] = None

    def __post_init__(self):
        self.episodes = [SeasonEpisode(**episode) if isinstance(episode, dict) else episode for episode in self.episodes]

def show_from_json(json_str: str) -> TmdbShow:
    try:
        return TmdbShow(**json.loads(json_str))
    except json.JSONDecodeError as e:
        raise f"Error decoding JSON: {e}"

def movie_from_json(json_str: str) -> TmdbMovie:
    try:
        return TmdbMovie(**json.loads(json_str))
    except json.JSONDecodeError as e:
        raise f"Error decoding JSON: {e}"
