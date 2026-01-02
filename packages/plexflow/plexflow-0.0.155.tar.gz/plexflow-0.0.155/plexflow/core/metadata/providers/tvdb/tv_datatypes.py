from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AirsDays:
    """
    Represents the days on which a TV show airs.

    Attributes:
        friday (Optional[bool]): Indicates if the show airs on Fridays.
        monday (Optional[bool]): Indicates if the show airs on Mondays.
        saturday (Optional[bool]): Indicates if the show airs on Saturdays.
        sunday (Optional[bool]): Indicates if the show airs on Sundays.
        thursday (Optional[bool]): Indicates if the show airs on Thursdays.
        tuesday (Optional[bool]): Indicates if the show airs on Tuesdays.
        wednesday (Optional[bool]): Indicates if the show airs on Wednesdays.
        _catchall (dict): Catch-all attribute for any additional data not defined in the class.
    """
    friday: Optional[bool] = None
    monday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    thursday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Alias:
    """
    Represents an alias for a TV show or character.
    
    Attributes:
        language (Optional[str]): The language of the alias.
        name (Optional[str]): The name of the alias.
        _catchall (dict): A catch-all field for any additional attributes.
    """
    language: Optional[str] = None
    name: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TagOption:
    """
    Represents a tag option for a TV show.

    Attributes:
        helpText (Optional[str]): The help text for the tag option.
        id (Optional[int]): The ID of the tag option.
        name (Optional[str]): The name of the tag option.
        tag (Optional[int]): The tag of the tag option.
        tagName (Optional[str]): The tag name of the tag option.
        _catchall (dict): A catch-all field for any additional attributes not defined in the class.
    """
    helpText: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    tag: Optional[int] = None
    tagName: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Status:
    """
    Represents the status of a TV show.

    Attributes:
        id (Optional[int]): The ID of the status.
        name (Optional[str]): The name of the status.
        _catchall (dict): A catch-all dictionary for any additional attributes.
    """
    id: Optional[int] = None
    name: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Artwork:
    """
    Represents artwork associated with a TV show.

    Attributes:
        episodeId (Optional[int]): The ID of the episode associated with the artwork.
        height (Optional[int]): The height of the artwork image.
        id (Optional[int]): The ID of the artwork.
        image (Optional[str]): The URL or path to the artwork image.
        includesText (Optional[bool]): Indicates whether the artwork includes text.
        language (Optional[str]): The language of the artwork.
        movieId (Optional[int]): The ID of the movie associated with the artwork.
        networkId (Optional[int]): The ID of the network associated with the artwork.
        peopleId (Optional[int]): The ID of the people associated with the artwork.
        score (Optional[int]): The score of the artwork.
        seasonId (Optional[int]): The ID of the season associated with the artwork.
        seriesId (Optional[int]): The ID of the series associated with the artwork.
        seriesPeopleId (Optional[int]): The ID of the series people associated with the artwork.
        status (Optional[Status]): The status of the artwork.
        tagOptions (Optional[List[TagOption]]): The tag options associated with the artwork.
        thumbnail (Optional[str]): The URL or path to the thumbnail image of the artwork.
        thumbnailHeight (Optional[int]): The height of the thumbnail image.
        thumbnailWidth (Optional[int]): The width of the thumbnail image.
        type (Optional[int]): The type of the artwork.
        updatedAt (Optional[int]): The timestamp of when the artwork was last updated.
        width (Optional[int]): The width of the artwork image.
        _catchall (dict): A catch-all field for any additional attributes not defined in the class.
    """

    episodeId: Optional[int] = None
    height: Optional[int] = None
    id: Optional[int] = None
    image: Optional[str] = None
    includesText: Optional[bool] = None
    language: Optional[str] = None
    movieId: Optional[int] = None
    networkId: Optional[int] = None
    peopleId: Optional[int] = None
    score: Optional[int] = None
    seasonId: Optional[int] = None
    seriesId: Optional[int] = None
    seriesPeopleId: Optional[int] = None
    status: Optional[Status] = None
    tagOptions: Optional[List[TagOption]] = None
    thumbnail: Optional[str] = None
    thumbnailHeight: Optional[int] = None
    thumbnailWidth: Optional[int] = None
    type: Optional[int] = None
    updatedAt: Optional[int] = None
    width: Optional[int] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.status = Status(**self.status) if isinstance(self.status, dict) else self.status
        self.tagOptions = [TagOption(**tagOption) if isinstance(tagOption, dict) else tagOption for tagOption in self.tagOptions] if self.tagOptions else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EpisodeInfo:
    """
    Represents information about an episode of a TV show.

    Attributes:
        image (Optional[str]): The image associated with the episode.
        name (Optional[str]): The name of the episode.
        year (Optional[str]): The year the episode was released.
        _catchall (dict): A catch-all dictionary for any additional attributes.
    """
    image: Optional[str] = None
    name: Optional[str] = None
    year: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Character:
    """
    Represents a character in a TV show.

    Attributes:
        aliases (Optional[List[Alias]]): List of aliases for the character.
        episode (Optional[EpisodeInfo]): Information about the episode the character appears in.
        episodeId (Optional[int]): ID of the episode the character appears in.
        id (Optional[int]): ID of the character.
        image (Optional[str]): URL of the character's image.
        isFeatured (Optional[bool]): Indicates if the character is featured.
        movieId (Optional[int]): ID of the movie the character appears in.
        movie (Optional[EpisodeInfo]): Information about the movie the character appears in.
        name (Optional[str]): Name of the character.
        nameTranslations (Optional[List[str]]): List of translated names for the character.
        overviewTranslations (Optional[List[str]]): List of translated overviews for the character.
        peopleId (Optional[int]): ID of the people associated with the character.
        personImgURL (Optional[str]): URL of the person's image associated with the character.
        peopleType (Optional[str]): Type of people associated with the character.
        seriesId (Optional[int]): ID of the TV series the character appears in.
        series (Optional[EpisodeInfo]): Information about the TV series the character appears in.
        sort (Optional[int]): Sort order of the character.
        tagOptions (Optional[List[TagOption]]): List of tag options for the character.
        type (Optional[int]): Type of the character.
        url (Optional[str]): URL of the character.
        personName (Optional[str]): Name of the person associated with the character.
        _catchall (dict): Catch-all field for any additional attributes not defined in the class.

    Methods:
        __post_init__(): Initializes the class instance and converts nested dictionaries to objects.
    """
    aliases: Optional[List[Alias]] = None
    episode: Optional[EpisodeInfo] = None
    episodeId: Optional[int] = None
    id: Optional[int] = None
    image: Optional[str] = None
    isFeatured: Optional[bool] = None
    movieId: Optional[int] = None
    movie: Optional[EpisodeInfo] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    overviewTranslations: Optional[List[str]] = None
    peopleId: Optional[int] = None
    personImgURL: Optional[str] = None
    peopleType: Optional[str] = None
    seriesId: Optional[int] = None
    series: Optional[EpisodeInfo] = None
    sort: Optional[int] = None
    tagOptions: Optional[List[TagOption]] = None
    type: Optional[int] = None
    url: Optional[str] = None
    personName: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.aliases = [Alias(**alias) if isinstance(alias, dict) else alias for alias in self.aliases] if self.aliases else []
        self.episode = EpisodeInfo(**self.episode) if isinstance(self.episode, dict) else self.episode
        self.movie = EpisodeInfo(**self.movie) if isinstance(self.movie, dict) else self.movie
        self.series = EpisodeInfo(**self.series) if isinstance(self.series, dict) else self.series
        self.tagOptions = [TagOption(**tagOption) if isinstance(tagOption, dict) else tagOption for tagOption in self.tagOptions] if self.tagOptions else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ContentRating:
    """
    Represents the content rating of a TV show.

    Attributes:
        id (Optional[int]): The ID of the content rating.
        name (Optional[str]): The name of the content rating.
        description (Optional[str]): The description of the content rating.
        country (Optional[str]): The country of the content rating.
        contentType (Optional[str]): The type of content the rating applies to.
        order (Optional[int]): The order of the content rating.
        fullName (Optional[str]): The full name of the content rating.
        _catchall (dict): A catch-all field for any additional attributes not defined in the class.
    """
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    contentType: Optional[str] = None
    order: Optional[int] = None
    fullName: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Company:
    """
    Represents a company associated with a TV show.
    """
    activeDate: Optional[str] = None
    aliases: Optional[List[Alias]] = None
    country: Optional[str] = None
    id: Optional[int] = None
    inactiveDate: Optional[str] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    overviewTranslations: Optional[List[str]] = None
    primaryCompanyType: Optional[int] = None
    slug: Optional[str] = None
    parentCompany: Optional[Status] = None
    tagOptions: Optional[List[TagOption]] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.aliases = [Alias(**alias) if isinstance(alias, dict) else alias for alias in self.aliases]
        self.parentCompany = Status(**self.parentCompany) if isinstance(self.parentCompany, dict) else self.parentCompany
        self.tagOptions = [TagOption(**tagOption) if isinstance(tagOption, dict) else tagOption for tagOption in self.tagOptions] if self.tagOptions else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Companies:
    """
    Represents the companies associated with a TV show.
    """
    studio: Optional[List[Company]] = None
    network: Optional[List[Company]] = None
    production: Optional[List[Company]] = None
    distributor: Optional[List[Company]] = None
    special_effects: Optional[List[Company]] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.studio = [Company(**company) if isinstance(company, dict) else company for company in self.studio] if self.studio else []
        self.network = [Company(**company) if isinstance(company, dict) else company for company in self.network] if self.network else []
        self.production = [Company(**company) if isinstance(company, dict) else company for company in self.production] if self.production else []
        self.distributor = [Company(**company) if isinstance(company, dict) else company for company in self.distributor] if self.distributor else []
        self.special_effects = [Company(**company) if isinstance(company, dict) else company for company in self.special_effects] if self.special_effects else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Type:
    """
    Represents the type of a TV show.
    """
    alternateName: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Season:
    """
    Represents a season of a TV show.
    """
    id: Optional[int] = None
    image: Optional[str] = None
    imageType: Optional[int] = None
    lastUpdated: Optional[str] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    number: Optional[int] = None
    overviewTranslations: Optional[List[str]] = None
    companies: Optional[Companies] = None
    seriesId: Optional[int] = None
    type: Optional[Type] = None
    year: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.companies = Companies(**self.companies) if isinstance(self.companies, dict) else self.companies
        self.type = Type(**self.type) if isinstance(self.type, dict) else self.type

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Episode:
    """
    Represents an episode of a TV show.
    """
    aired: Optional[str] = None
    airsAfterSeason: Optional[int] = None
    airsBeforeEpisode: Optional[int] = None
    airsBeforeSeason: Optional[int] = None
    finaleType: Optional[str] = None
    id: Optional[int] = None
    image: Optional[str] = None
    imageType: Optional[int] = None
    isMovie: Optional[int] = None
    lastUpdated: Optional[str] = None
    linkedMovie: Optional[int] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    number: Optional[int] = None
    overview: Optional[str] = None
    overviewTranslations: Optional[List[str]] = None
    runtime: Optional[int] = None
    seasonNumber: Optional[int] = None
    seasons: Optional[List[Season]] = None
    seriesId: Optional[int] = None
    seasonName: Optional[str] = None
    year: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.seasons = [Season(**season) if isinstance(season, dict) else season for season in self.seasons] if self.seasons else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ListAlias:
    """
    Represents an alias for a TV show list.
    """
    language: Optional[str] = None
    name: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RemoteId:
    """
    Represents a remote ID for a TV show.
    """
    id: Optional[str] = None
    type: Optional[int] = None
    sourceName: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TvdbList:
    """
    Represents a TV show list.
    """
    aliases: Optional[List[ListAlias]] = None
    id: Optional[int] = None
    image: Optional[str] = None
    imageIsFallback: Optional[bool] = None
    isOfficial: Optional[bool] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    overview: Optional[str] = None
    overviewTranslations: Optional[List[str]] = None
    remoteIds: Optional[List[RemoteId]] = None
    tags: Optional[List[TagOption]] = None
    score: Optional[int] = None
    url: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.aliases = [ListAlias(**alias) if isinstance(alias, dict) else alias for alias in self.aliases]
        self.remoteIds = [RemoteId(**remoteId) if isinstance(remoteId, dict) else remoteId for remoteId in self.remoteIds] if self.remoteIds else []
        self.tags = [TagOption(**tag) if isinstance(tag, dict) else tag for tag in self.tags] if self.tags else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Genre:
    id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Translation:
    aliases: Optional[List[str]] = None
    isAlias: Optional[bool] = None
    isPrimary: Optional[bool] = None
    language: Optional[str] = None
    name: Optional[str] = None
    overview: Optional[str] = None
    tagline: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Translations:
    nameTranslations: Optional[List[Translation]] = None
    overviewTranslations: Optional[List[Translation]] = None
    alias: Optional[List[str]] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.nameTranslations = [Translation(**translation) if isinstance(translation, dict) else translation for translation in self.nameTranslations]
        self.overviewTranslations = [Translation(**translation) if isinstance(translation, dict) else translation for translation in self.overviewTranslations]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Trailer:
    id: Optional[int] = None
    language: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    runtime: Optional[int] = None
    _catchall: dict = field(default_factory=dict, repr=False)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TvdbShow:
    """
    Represents a TV show retrieved from the TVDB API.

    Attributes:
        abbreviation (Optional[str]): The abbreviation of the show.
        airsDays (Optional[AirsDays]): The days on which the show airs.
        airsTime (Optional[str]): The time at which the show airs.
        aliases (Optional[List[Alias]]): The aliases of the show.
        artworks (Optional[List[Artwork]]): The artworks associated with the show.
        averageRuntime (Optional[int]): The average runtime of the show in minutes.
        characters (Optional[List[Character]]): The characters in the show.
        contentRatings (Optional[List[ContentRating]]): The content ratings of the show.
        country (Optional[str]): The country in which the show is produced.
        defaultSeasonType (Optional[int]): The default season type of the show.
        episodes (Optional[List[Episode]]): The episodes of the show.
        firstAired (Optional[str]): The date on which the show first aired.
        lists (Optional[List[TvdbList]]): The lists associated with the show.
        genres (Optional[List[Genre]]): The genres of the show.
        id (Optional[int]): The ID of the show.
        image (Optional[str]): The image associated with the show.
        isOrderRandomized (Optional[bool]): Indicates if the episode order is randomized.
        lastAired (Optional[str]): The date on which the show last aired.
        lastUpdated (Optional[str]): The date on which the show was last updated.
        name (Optional[str]): The name of the show.
        nameTranslations (Optional[List[str]]): The translations of the show's name.
        companies (Optional[List[Company]]): The companies associated with the show.
        nextAired (Optional[str]): The date on which the next episode airs.
        originalCountry (Optional[str]): The original country of the show.
        originalLanguage (Optional[str]): The original language of the show.
        originalNetwork (Optional[Company]): The original network of the show.
        overview (Optional[str]): The overview of the show.
        latestNetwork (Optional[Company]): The latest network of the show.
        overviewTranslations (Optional[List[str]]): The translations of the show's overview.
        remoteIds (Optional[List[RemoteId]]): The remote IDs associated with the show.
        score (Optional[int]): The score of the show.
        seasons (Optional[List[Season]]): The seasons of the show.
        seasonTypes (Optional[List[Type]]): The types of seasons in the show.
        slug (Optional[str]): The slug of the show.
        status (Optional[Status]): The status of the show.
        tags (Optional[List[TagOption]]): The tags associated with the show.
        trailers (Optional[List[Trailer]]): The trailers of the show.
        translations (Optional[Translations]): The translations of the show.
        year (Optional[str]): The year in which the show was released.
        _catchall (dict): A catch-all field for any additional attributes.
    """
    abbreviation: Optional[str] = None
    airsDays: Optional[AirsDays] = None
    airsTime: Optional[str] = None
    aliases: Optional[List[Alias]] = None
    artworks: Optional[List[Artwork]] = None
    averageRuntime: Optional[int] = None
    characters: Optional[List[Character]] = None
    contentRatings: Optional[List[ContentRating]] = None
    country: Optional[str] = None
    defaultSeasonType: Optional[int] = None
    episodes: Optional[List[Episode]] = None
    firstAired: Optional[str] = None
    lists: Optional[List[TvdbList]] = None
    genres: Optional[List[Genre]] = None
    id: Optional[int] = None
    image: Optional[str] = None
    isOrderRandomized: Optional[bool] = None
    lastAired: Optional[str] = None
    lastUpdated: Optional[str] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    companies: Optional[List[Company]] = None
    nextAired: Optional[str] = None
    originalCountry: Optional[str] = None
    originalLanguage: Optional[str] = None
    originalNetwork: Optional[Company] = None
    overview: Optional[str] = None
    latestNetwork: Optional[Company] = None
    overviewTranslations: Optional[List[str]] = None
    remoteIds: Optional[List[RemoteId]] = None
    score: Optional[int] = None
    seasons: Optional[List[Season]] = None
    seasonTypes: Optional[List[Type]] = None
    slug: Optional[str] = None
    status: Optional[Status] = None
    tags: Optional[List[TagOption]] = None
    trailers: Optional[List[Trailer]] = None
    translations: Optional[Translations] = None
    year: Optional[str] = None
    _catchall: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.airsDays = AirsDays(**self.airsDays) if isinstance(self.airsDays, dict) else self.airsDays
        self.aliases = [Alias(**alias) if isinstance(alias, dict) else alias for alias in self.aliases]
        self.artworks = [Artwork(**artwork) if isinstance(artwork, dict) else artwork for artwork in self.artworks] if self.artworks else []
        self.characters = [Character(**character) if isinstance(character, dict) else character for character in self.characters] if self.characters else []
        self.contentRatings = [ContentRating(**contentRating) if isinstance(contentRating, dict) else contentRating for contentRating in self.contentRatings]
        self.episodes = [Episode(**episode) if isinstance(episode, dict) else episode for episode in self.episodes] if self.episodes else []
        self.lists = [TvdbList(**list) if isinstance(list, dict) else list for list in self.lists]
        self.genres = [Genre(**genre) if isinstance(genre, dict) else genre for genre in self.genres]
        self.companies = [Company(**company) if isinstance(company, dict) else company for company in self.companies]
        self.originalNetwork = Company(**self.originalNetwork) if isinstance(self.originalNetwork, dict) else self.originalNetwork
        self.latestNetwork = Company(**self.latestNetwork) if isinstance(self.latestNetwork, dict) else self.latestNetwork
        self.remoteIds = [RemoteId(**remoteId) if isinstance(remoteId, dict) else remoteId for remoteId in self.remoteIds]
        self.seasons = [Season(**season) if isinstance(season, dict) else season for season in self.seasons]
        self.seasonTypes = [Type(**type) if isinstance(type, dict) else type for type in self.seasonTypes]
        self.status = Status(**self.status) if isinstance(self.status, dict) else self.status
        self.tags = [TagOption(**tag) if isinstance(tag, dict) else tag for tag in self.tags] if self.tags else []
        self.trailers = [Trailer(**trailer) if isinstance(trailer, dict) else trailer for trailer in self.trailers]
        self.translations = Translations(**self.translations) if isinstance(self.translations, dict) else self.translations
