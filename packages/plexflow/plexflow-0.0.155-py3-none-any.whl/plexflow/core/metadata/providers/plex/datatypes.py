from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexImage:
    """
    Represents an image in Plex metadata.

    Attributes:
        alt (Optional[str]): The alternative text for the image.
        type (Optional[str]): The type of the image.
        url (Optional[str]): The URL of the image.
    """
    alt: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexGenre:
    """
    Represents a genre in Plex metadata.

    Attributes:
        filter (Optional[str]): The filter associated with the genre.
        id (Optional[str]): The ID of the genre.
        ratingKey (Optional[str]): The rating key of the genre.
        slug (Optional[str]): The slug of the genre.
        tag (Optional[str]): The tag of the genre.
        type (Optional[str]): The type of the genre.
        context (Optional[str]): The context of the genre.
    """
    filter: Optional[str] = None
    id: Optional[str] = None
    ratingKey: Optional[str] = None
    slug: Optional[str] = None
    tag: Optional[str] = None
    type: Optional[str] = None
    context: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexGuid:
    """
    Represents a Plex GUID.

    Attributes:
        id (Optional[str]): The ID of the Plex GUID.
    """
    id: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexCollection:
    """
    Represents a collection in Plex.

    Attributes:
        art (Optional[str]): The URL of the collection's artwork.
        guid (Optional[str]): The unique identifier of the collection.
        key (Optional[str]): The key of the collection.
        summary (Optional[str]): A summary or description of the collection.
        thumb (Optional[str]): The URL of the collection's thumbnail.
        tag (Optional[str]): A tag associated with the collection.
    """
    art: Optional[str] = None
    guid: Optional[str] = None
    key: Optional[str] = None
    summary: Optional[str] = None
    thumb: Optional[str] = None
    tag: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexCountry:
    """
    Represents a country in the Plex metadata.

    Attributes:
        tag (Optional[str]): The tag of the country.
    """
    tag: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexRole:
    """
    Represents a role in Plex metadata.

    Attributes:
        key (Optional[str]): The key of the role.
        id (Optional[str]): The ID of the role.
        order (Optional[int]): The order of the role.
        slug (Optional[str]): The slug of the role.
        tag (Optional[str]): The tag of the role.
        thumb (Optional[str]): The thumbnail of the role.
        role (Optional[str]): The role name.
        type (Optional[str]): The type of the role.
    """
    key: Optional[str] = None
    id: Optional[str] = None
    order: Optional[int] = None
    slug: Optional[str] = None
    tag: Optional[str] = None
    thumb: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexDirector:
    """
    Represents a director in Plex metadata.

    Attributes:
        key (Optional[str]): The key of the director.
        id (Optional[str]): The ID of the director.
        slug (Optional[str]): The slug of the director.
        tag (Optional[str]): The tag of the director.
        thumb (Optional[str]): The thumbnail URL of the director.
        role (Optional[str]): The role of the director.
        type (Optional[str]): The type of the director.
    """
    key: Optional[str] = None
    id: Optional[str] = None
    slug: Optional[str] = None
    tag: Optional[str] = None
    thumb: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexProducer:
    """
    Represents a producer in Plex metadata.

    Attributes:
        key (Optional[str]): The key of the producer.
        id (Optional[str]): The ID of the producer.
        slug (Optional[str]): The slug of the producer.
        tag (Optional[str]): The tag of the producer.
        role (Optional[str]): The role of the producer.
        type (Optional[str]): The type of the producer.
    """
    key: Optional[str] = None
    id: Optional[str] = None
    slug: Optional[str] = None
    tag: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexWriter:
    """
    Represents a writer in the Plex metadata provider.

    Attributes:
        key (Optional[str]): The key of the writer.
        id (Optional[str]): The ID of the writer.
        slug (Optional[str]): The slug of the writer.
        tag (Optional[str]): The tag of the writer.
        thumb (Optional[str]): The thumbnail URL of the writer.
        role (Optional[str]): The role of the writer.
        type (Optional[str]): The type of the writer.
    """
    key: Optional[str] = None
    id: Optional[str] = None
    slug: Optional[str] = None
    tag: Optional[str] = None
    thumb: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexRating:
    """
    Represents a rating for a Plex item.

    Attributes:
        image (Optional[str]): The URL of the rating image.
        type (Optional[str]): The type of the rating.
        value (Optional[float]): The value of the rating.
    """
    image: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexStudio:
    """
    Represents a studio in Plex.

    Attributes:
        tag (Optional[str]): The tag of the studio.
    """
    tag: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexMovieMetadata:
    """
    Represents the metadata for a movie in Plex.

    Attributes:
        art (Optional[str]): The URL of the movie's artwork.
        guid (Optional[str]): The unique identifier of the movie.
        key (Optional[str]): The key of the movie in Plex.
        primaryExtraKey (Optional[str]): The key of the primary extra associated with the movie.
        rating (Optional[float]): The rating of the movie.
        ratingKey (Optional[str]): The key of the rating in Plex.
        studio (Optional[str]): The studio that produced the movie.
        summary (Optional[str]): The summary of the movie.
        tagline (Optional[str]): The tagline of the movie.
        type (Optional[str]): The type of the movie.
        thumb (Optional[str]): The URL of the movie's thumbnail.
        addedAt (Optional[int]): The timestamp when the movie was added.
        duration (Optional[int]): The duration of the movie in seconds.
        publicPagesURL (Optional[str]): The URL of the movie's public page.
        slug (Optional[str]): The slug of the movie.
        userState (Optional[bool]): The user state of the movie.
        title (Optional[str]): The title of the movie.
        contentRating (Optional[str]): The content rating of the movie.
        originallyAvailableAt (Optional[str]): The original release date of the movie.
        year (Optional[int]): The year the movie was released.
        audienceRating (Optional[float]): The audience rating of the movie.
        audienceRatingImage (Optional[str]): The URL of the audience rating image.
        ratingImage (Optional[str]): The URL of the rating image.
        imdbRatingCount (Optional[int]): The number of IMDb ratings for the movie.
        source (Optional[str]): The source of the movie.
        Image (Optional[List[PlexImage]]): The list of images associated with the movie.
        Genre (Optional[List[PlexGenre]]): The list of genres of the movie.
        Guid (Optional[List[PlexGuid]]): The list of GUIDs associated with the movie.
        Collection (Optional[List[PlexCollection]]): The list of collections the movie belongs to.
        Country (Optional[List[PlexCountry]]): The list of countries associated with the movie.
        Role (Optional[List[PlexRole]]): The list of roles in the movie.
        Director (Optional[List[PlexDirector]]): The list of directors of the movie.
        Producer (Optional[List[PlexProducer]]): The list of producers of the movie.
        Writer (Optional[List[PlexWriter]]): The list of writers of the movie.
        Rating (Optional[List[PlexRating]]): The list of ratings of the movie.
        Studio (Optional[List[PlexStudio]]): The list of studios associated with the movie.
    """
    title: Optional[str] = field(default=None)
    guid: Optional[str] = field(default=None)
    key: Optional[str] = field(default=None)
    primaryExtraKey: Optional[str] = field(default=None)
    rating: Optional[float] = field(default=None)
    ratingKey: Optional[str] = field(default=None)
    studio: Optional[str] = field(default=None)
    summary: Optional[str] = field(default=None)
    tagline: Optional[str] = field(default=None)
    type: Optional[str] = field(default=None)
    thumb: Optional[str] = field(default=None)
    addedAt: Optional[int] = field(default=None)
    duration: Optional[int] = field(default=None)
    publicPagesURL: Optional[str] = field(default=None)
    slug: Optional[str] = field(default=None)
    userState: Optional[bool] = field(default=None)
    contentRating: Optional[str] = field(default=None)
    originallyAvailableAt: Optional[str] = field(default=None)
    year: Optional[int] = field(default=None)
    audienceRating: Optional[float] = None
    audienceRatingImage: Optional[str] = None
    ratingImage: Optional[str] = None
    imdbRatingCount: Optional[int] = None
    source: Optional[str] = field(default=None)
    Image: Optional[List[PlexImage]] = field(default=None)
    Genre: Optional[List[PlexGenre]] = field(default=None)
    Guid: Optional[List[PlexGuid]] = field(default=None)
#    Collection: Optional[List[PlexCollection]]
    Country: Optional[List[PlexCountry]] = field(default=None)
    Role: Optional[List[PlexRole]] = field(default=None)
    Director: Optional[List[PlexDirector]] = field(default=None)
    Producer: Optional[List[PlexProducer]] = field(default=None)
    Writer: Optional[List[PlexWriter]] = field(default=None)
    Rating: Optional[List[PlexRating]] = field(default=None)
    Studio: Optional[List[PlexStudio]] = field(default=None)

    def __post_init__(self):
        self.Image = [PlexImage(**image) if isinstance(image, dict) else image for image in self.Image] if self.Image else []
        self.Genre = [PlexGenre(**genre) if isinstance(genre, dict) else genre for genre in self.Genre] if self.Genre else []
        self.Guid = [PlexGuid(**guid) if isinstance(guid, dict) else guid for guid in self.Guid] if self.Guid else []
#        self.Collection = [PlexCollection(**collection) if isinstance(collection, dict) else collection for collection in self.Collection]
        self.Country = [PlexCountry(**country) if isinstance(country, dict) else country for country in self.Country] if self.Country else []
        self.Role = [PlexRole(**role) if isinstance(role, dict) else role for role in self.Role] if self.Role else []
        self.Director = [PlexDirector(**director) if isinstance(director, dict) else director for director in self.Director] if self.Director else []
        self.Producer = [PlexProducer(**producer) if isinstance(producer, dict) else producer for producer in self.Producer] if self.Producer else []
        self.Writer = [PlexWriter(**writer) if isinstance(writer, dict) else writer for writer in self.Writer] if self.Writer else []
        self.Rating = [PlexRating(**rating) if isinstance(rating, dict) else rating for rating in self.Rating] if self.Rating else []
        self.Studio = [PlexStudio(**studio) if isinstance(studio, dict) else studio for studio in self.Studio] if self.Studio else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MovieMediaContainer:
    """
    Represents a container for movie media metadata in Plex.

    Attributes:
        offset (Optional[int]): The offset value.
        totalSize (Optional[int]): The total size value.
        identifier (Optional[str]): The identifier value.
        size (Optional[int]): The size value.
        Metadata (Optional[List[PlexMovieMetadata]]): A list of PlexMovieMetadata objects representing the movie metadata.

    Methods:
        __post_init__(): Initializes the MovieMediaContainer object and converts the metadata dictionaries to PlexMovieMetadata objects.
    """
    offset: Optional[int] = None
    totalSize: Optional[int] = None
    identifier: Optional[str] = None
    size: Optional[int] = None
    Metadata: Optional[List[PlexMovieMetadata]] = None

    def __post_init__(self):
        self.Metadata = [PlexMovieMetadata(**metadata) if isinstance(metadata, dict) else metadata for metadata in self.Metadata]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexShowMetadata:
    """
    Represents the metadata for a TV show in Plex.

    Attributes:
        art (Optional[str]): The URL of the artwork for the show.
        guid (Optional[str]): The unique identifier for the show.
        key (Optional[str]): The key of the show.
        primaryExtraKey (Optional[str]): The key of the primary extra associated with the show.
        rating (Optional[float]): The rating of the show.
        ratingKey (Optional[str]): The key of the rating for the show.
        studio (Optional[str]): The studio that produced the show.
        subtype (Optional[str]): The subtype of the show.
        summary (Optional[str]): The summary of the show.
        tagline (Optional[str]): The tagline of the show.
        type (Optional[str]): The type of the show.
        thumb (Optional[str]): The URL of the thumbnail for the show.
        addedAt (Optional[int]): The timestamp when the show was added.
        duration (Optional[int]): The duration of the show.
        publicPagesURL (Optional[str]): The URL of the public pages for the show.
        slug (Optional[str]): The slug of the show.
        userState (Optional[bool]): The user state of the show.
        title (Optional[str]): The title of the show.
        leafCount (Optional[int]): The number of leaf items in the show.
        childCount (Optional[int]): The number of child items in the show.
        skipChildren (Optional[bool]): Indicates whether to skip child items.
        isContinuingSeries (Optional[bool]): Indicates whether the show is a continuing series.
        contentRating (Optional[str]): The content rating of the show.
        originallyAvailableAt (Optional[str]): The original release date of the show.
        year (Optional[int]): The year the show was released.
        ratingImage (Optional[str]): The URL of the rating image for the show.
        imdbRatingCount (Optional[int]): The number of IMDb ratings for the show.
        source (Optional[str]): The source of the show.
        Image (Optional[List[PlexImage]]): The list of images associated with the show.
        Genre (Optional[List[PlexGenre]]): The list of genres for the show.
        Guid (Optional[List[PlexGuid]]): The list of GUIDs for the show.
        Country (Optional[List[PlexCountry]]): The list of countries for the show.
        Role (Optional[List[PlexRole]]): The list of roles for the show.
        Director (Optional[List[PlexDirector]]): The list of directors for the show.
        Producer (Optional[List[PlexProducer]]): The list of producers for the show.
        Writer (Optional[List[PlexWriter]]): The list of writers for the show.
        Rating (Optional[List[PlexRating]]): The list of ratings for the show.
        Studio (Optional[List[PlexStudio]]): The list of studios for the show.
        _catchall (dict): A catch-all dictionary for any additional attributes.
    """

    art: Optional[str] = None
    guid: Optional[str] = None
    key: Optional[str] = None
    primaryExtraKey: Optional[str] = None
    rating: Optional[float] = None
    ratingKey: Optional[str] = None
    studio: Optional[str] = None
    subtype: Optional[str] = None
    summary: Optional[str] = None
    tagline: Optional[str] = None
    type: Optional[str] = None
    thumb: Optional[str] = None
    addedAt: Optional[int] = None
    duration: Optional[int] = None
    publicPagesURL: Optional[str] = None
    slug: Optional[str] = None
    userState: Optional[bool] = None
    title: Optional[str] = None
    leafCount: Optional[int] = None
    childCount: Optional[int] = None
    skipChildren: Optional[bool] = None
    isContinuingSeries: Optional[bool] = None
    contentRating: Optional[str] = None
    originallyAvailableAt: Optional[str] = None
    year: Optional[int] = None
    ratingImage: Optional[str] = None
    imdbRatingCount: Optional[int] = None
    source: Optional[str] = None
    Image: Optional[List[PlexImage]] = None
    Guid: Optional[List[PlexGuid]] = None
    Role: Optional[List[PlexRole]] = None
    Country: Optional[List[PlexCountry]] = None
    Director: Optional[List[PlexDirector]] = None
    Writer: Optional[List[PlexWriter]] = None
    Rating: Optional[List[PlexRating]] = None
    Studio: Optional[List[PlexStudio]] = None
    Producer: Optional[List[PlexProducer]] = None
    Genre: Optional[List[PlexGenre]] = None
    _catchall: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.Image = [PlexImage(**image) if isinstance(image, dict) else image for image in self.Image] if self.Image else []
        self.Genre = [PlexGenre(**genre) if isinstance(genre, dict) else genre for genre in self.Genre] if self.Genre else []
        self.Guid = [PlexGuid(**guid) if isinstance(guid, dict) else guid for guid in self.Guid] if self.Guid else []
        self.Country = [PlexCountry(**country) if isinstance(country, dict) else country for country in self.Country] if self.Country else []
        self.Role = [PlexRole(**role) if isinstance(role, dict) else role for role in self.Role] if self.Role else []
        self.Director = [PlexDirector(**director) if isinstance(director, dict) else director for director in self.Director] if self.Director else []
        self.Producer = [PlexProducer(**producer) if isinstance(producer, dict) else producer for producer in self.Producer] if self.Producer else []
        self.Writer = [PlexWriter(**writer) if isinstance(writer, dict) else writer for writer in self.Writer] if self.Writer else []
        self.Rating = [PlexRating(**rating) if isinstance(rating, dict) else rating for rating in self.Rating] if self.Rating else []
        self.Studio = [PlexStudio(**studio) if isinstance(studio, dict) else studio for studio in self.Studio] if self.Studio else []


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ShowMediaContainer:
    """
    Represents a media container for TV shows in Plex.

    Attributes:
        offset (Optional[int]): The offset value.
        totalSize (Optional[int]): The total size value.
        identifier (Optional[str]): The identifier value.
        size (Optional[int]): The size value.
        Metadata (Optional[List[PlexShowMetadata]]): A list of PlexShowMetadata objects representing the metadata for the TV shows.

    Methods:
        __post_init__(): Initializes the ShowMediaContainer object and converts the metadata dictionaries to PlexShowMetadata objects.
    """
    offset: Optional[int] = None
    totalSize: Optional[int] = None
    identifier: Optional[str] = None
    size: Optional[int] = None
    Metadata: Optional[List[PlexShowMetadata]] = None

    def __post_init__(self):
        self.Metadata = [PlexShowMetadata(**metadata) if isinstance(metadata, dict) else metadata for metadata in self.Metadata]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexSeasonMetadata:
    """
    Represents the metadata for a season in Plex.

    Attributes:
        art (Optional[str]): The URL of the artwork for the season.
        guid (Optional[str]): The unique identifier of the season.
        key (Optional[str]): The key of the season.
        primaryExtraKey (Optional[str]): The key of the primary extra associated with the season.
        ratingKey (Optional[str]): The rating key of the season.
        summary (Optional[str]): The summary of the season.
        type (Optional[str]): The type of the season.
        thumb (Optional[str]): The URL of the thumbnail for the season.
        addedAt (Optional[int]): The timestamp when the season was added.
        publicPagesURL (Optional[str]): The public pages URL for the season.
        userState (Optional[bool]): The user state of the season.
        title (Optional[str]): The title of the season.
        parentSlug (Optional[str]): The slug of the parent item.
        parentTitle (Optional[str]): The title of the parent item.
        parentType (Optional[str]): The type of the parent item.
        parentArt (Optional[str]): The URL of the artwork for the parent item.
        parentThumb (Optional[str]): The URL of the thumbnail for the parent item.
        parentRatingKey (Optional[str]): The rating key of the parent item.
        parentGuid (Optional[str]): The unique identifier of the parent item.
        parentKey (Optional[str]): The key of the parent item.
        leafCount (Optional[int]): The number of leaf items in the season.
        index (Optional[int]): The index of the season.
        contentRating (Optional[str]): The content rating of the season.
        originallyAvailableAt (Optional[str]): The original release date of the season.
        year (Optional[int]): The year of the season.
        source (Optional[str]): The source of the season.
        Image (Optional[List[PlexImage]]): The list of images associated with the season.
        Guid (Optional[List[PlexGuid]]): The list of GUIDs associated with the season.
        Role (Optional[List[PlexRole]]): The list of roles associated with the season.
        Producer (Optional[List[PlexProducer]]): The list of producers associated with the season.
        _catchall (dict): A catch-all field for any additional attributes not defined in the class.

    Methods:
        __post_init__: Initializes the class and converts nested dictionaries to objects.
    """

    art: Optional[str] = None
    guid: Optional[str] = None
    key: Optional[str] = None
    primaryExtraKey: Optional[str] = None
    ratingKey: Optional[str] = None
    summary: Optional[str] = None
    type: Optional[str] = None
    thumb: Optional[str] = None
    addedAt: Optional[int] = None
    publicPagesURL: Optional[str] = None
    userState: Optional[bool] = None
    title: Optional[str] = None
    parentSlug: Optional[str] = None
    parentTitle: Optional[str] = None
    parentType: Optional[str] = None
    parentArt: Optional[str] = None
    parentThumb: Optional[str] = None
    parentRatingKey: Optional[str] = None
    parentGuid: Optional[str] = None
    parentKey: Optional[str] = None
    leafCount: Optional[int] = None
    index: Optional[int] = None
    contentRating: Optional[str] = None
    originallyAvailableAt: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None
    Image: Optional[List[PlexImage]] = None
    Guid: Optional[List[PlexGuid]] = None
    Role: Optional[List[PlexRole]] = None
    Producer: Optional[List[PlexProducer]] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Initializes the PlexSeasonMetadata class and converts nested dictionaries to objects.
        """
        self.Image = [PlexImage(**image) if isinstance(image, dict) else image for image in self.Image]
        self.Guid = [PlexGuid(**guid) if isinstance(guid, dict) else guid for guid in self.Guid]
        self.Role = [PlexRole(**role) if isinstance(role, dict) else role for role in self.Role] if self.Role else []
        self.Producer = [PlexProducer(**producer) if isinstance(producer, dict) else producer for producer in self.Producer] if self.Producer else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SeasonMediaContainer:
    """
    Represents a media container for a season in Plex.

    Attributes:
        offset (Optional[int]): The offset value.
        totalSize (Optional[int]): The total size value.
        identifier (Optional[str]): The identifier value.
        size (Optional[int]): The size value.
        Metadata (Optional[List[PlexSeasonMetadata]]): A list of PlexSeasonMetadata objects.
        _catchall (dict): A catch-all dictionary for additional attributes.

    Methods:
        __post_init__(): Initializes the SeasonMediaContainer object and converts the Metadata list to PlexSeasonMetadata objects.
    """
    offset: Optional[int] = None
    totalSize: Optional[int] = None
    identifier: Optional[str] = None
    size: Optional[int] = None
    Metadata: Optional[List[PlexSeasonMetadata]] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        self.Metadata = [PlexSeasonMetadata(**metadata) if isinstance(metadata, dict) else metadata for metadata in self.Metadata]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexEpisodeMetadata:
    """
    Represents the metadata for a Plex episode.

    Attributes:
        guid (Optional[str]): The unique identifier for the episode.
        key (Optional[str]): The key of the episode.
        rating (Optional[int]): The rating of the episode.
        ratingKey (Optional[str]): The rating key of the episode.
        summary (Optional[str]): The summary of the episode.
        type (Optional[str]): The type of the episode.
        thumb (Optional[str]): The thumbnail image URL of the episode.
        addedAt (Optional[int]): The timestamp when the episode was added.
        duration (Optional[int]): The duration of the episode in seconds.
        publicPagesURL (Optional[str]): The public pages URL of the episode.
        userState (Optional[bool]): The user state of the episode.
        title (Optional[str]): The title of the episode.
        grandparentTitle (Optional[str]): The title of the grandparent of the episode.
        grandparentSlug (Optional[str]): The slug of the grandparent of the episode.
        grandparentType (Optional[str]): The type of the grandparent of the episode.
        grandparentArt (Optional[str]): The artwork URL of the grandparent of the episode.
        grandparentThumb (Optional[str]): The thumbnail image URL of the grandparent of the episode.
        grandparentRatingKey (Optional[str]): The rating key of the grandparent of the episode.
        grandparentGuid (Optional[str]): The guid of the grandparent of the episode.
        grandparentKey (Optional[str]): The key of the grandparent of the episode.
        parentTitle (Optional[str]): The title of the parent of the episode.
        parentType (Optional[str]): The type of the parent of the episode.
        parentArt (Optional[str]): The artwork URL of the parent of the episode.
        parentThumb (Optional[str]): The thumbnail image URL of the parent of the episode.
        parentRatingKey (Optional[str]): The rating key of the parent of the episode.
        parentGuid (Optional[str]): The guid of the parent of the episode.
        parentKey (Optional[str]): The key of the parent of the episode.
        index (Optional[int]): The index of the episode.
        parentIndex (Optional[int]): The index of the parent of the episode.
        contentRating (Optional[str]): The content rating of the episode.
        originallyAvailableAt (Optional[str]): The original release date of the episode.
        year (Optional[int]): The year of the episode.
        ratingImage (Optional[str]): The rating image URL of the episode.
        source (Optional[str]): The source of the episode.
        Image (Optional[List[PlexImage]]): The list of images associated with the episode.
        Guid (Optional[List[PlexGuid]]): The list of GUIDs associated with the episode.
        Role (Optional[List[PlexRole]]): The list of roles associated with the episode.
        Director (Optional[List[PlexDirector]]): The list of directors associated with the episode.
        Writer (Optional[List[PlexWriter]]): The list of writers associated with the episode.
        Rating (Optional[List[PlexRating]]): The list of ratings associated with the episode.
        _catchall (dict): A catch-all dictionary for additional attributes.

    Methods:
        __post_init__(): Initializes the PlexEpisodeMetadata object and converts the Image, Guid, Role, Director, Writer, and Rating lists to their respective objects.
    """

    guid: Optional[str] = None
    key: Optional[str] = None
    rating: Optional[int] = None
    ratingKey: Optional[str] = None
    summary: Optional[str] = None
    type: Optional[str] = None
    thumb: Optional[str] = None
    addedAt: Optional[int] = None
    duration: Optional[int] = None
    publicPagesURL: Optional[str] = None
    userState: Optional[bool] = None
    title: Optional[str] = None
    grandparentTitle: Optional[str] = None
    grandparentSlug: Optional[str] = None
    grandparentType: Optional[str] = None
    grandparentArt: Optional[str] = None
    grandparentThumb: Optional[str] = None
    grandparentRatingKey: Optional[str] = None
    grandparentGuid: Optional[str] = None
    grandparentKey: Optional[str] = None
    parentTitle: Optional[str] = None
    parentType: Optional[str] = None
    parentArt: Optional[str] = None
    parentThumb: Optional[str] = None
    parentRatingKey: Optional[str] = None
    parentGuid: Optional[str] = None
    parentKey: Optional[str] = None
    index: Optional[int] = None
    parentIndex: Optional[int] = None
    contentRating: Optional[str] = None
    originallyAvailableAt: Optional[str] = None
    year: Optional[int] = None
    ratingImage: Optional[str] = None
    source: Optional[str] = None
    Image: Optional[List[PlexImage]] = None
    Guid: Optional[List[PlexGuid]] = None
    Role: Optional[List[PlexRole]] = None
    Director: Optional[List[PlexDirector]] = None
    Writer: Optional[List[PlexWriter]] = None
    Rating: Optional[List[PlexRating]] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        self.Image = [PlexImage(**image) if isinstance(image, dict) else image for image in self.Image] if self.Image else []
        self.Guid = [PlexGuid(**guid) if isinstance(guid, dict) else guid for guid in self.Guid]
        self.Role = [PlexRole(**role) if isinstance(role, dict) else role for role in self.Role] if self.Role else []
        self.Director = [PlexDirector(**director) if isinstance(director, dict) else director for director in self.Director] if self.Director else []
        self.Writer = [PlexWriter(**writer) if isinstance(writer, dict) else writer for writer in self.Writer] if self.Writer else []
        self.Rating = [PlexRating(**rating) if isinstance(rating, dict) else rating for rating in self.Rating] if self.Rating else []

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EpisodeMediaContainer:
    """
    Represents a container for episode media information.

    Attributes:
        offset (Optional[int]): The offset value.
        totalSize (Optional[int]): The total size value.
        identifier (Optional[str]): The identifier value.
        size (Optional[int]): The size value.
        Metadata (Optional[List[PlexEpisodeMetadata]]): A list of PlexEpisodeMetadata objects.
        _catchall (dict): A catch-all dictionary for additional attributes.

    Methods:
        __post_init__(): Initializes the EpisodeMediaContainer object and processes the Metadata attribute.
    """
    offset: Optional[int] = None
    totalSize: Optional[int] = None
    identifier: Optional[str] = None
    size: Optional[int] = None
    Metadata: Optional[List[PlexEpisodeMetadata]] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        self.Metadata = [PlexEpisodeMetadata(**metadata) if isinstance(metadata, dict) else metadata for metadata in self.Metadata]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlexUserState:
    """
    Represents the state of a Plex user for a specific media item.

    Attributes:
        grandparentWatchlistedAt (Optional[int]): The timestamp when the media item was watchlisted by the user.
        viewCount (Optional[int]): The number of times the user has viewed the media item.
        viewOffset (Optional[int]): The playback position (in milliseconds) where the user left off in the media item.
        lastViewedAt (Optional[int]): The timestamp when the user last viewed the media item.
    """
    grandparentWatchlistedAt: Optional[int] = None
    viewCount: Optional[int] = None
    viewOffset: Optional[int] = None
    lastViewedAt: Optional[int] = None
    viewState: Optional[str] = None
    ratingKey: Optional[str] = None
    type: Optional[str] = None
    _catchall: dict = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class WatchStateMediaContainer:
    """
    Represents the watch state of a media container in Plex.

    Attributes:
        identifier (Optional[str]): The identifier of the media container.
        size (Optional[int]): The size of the media container.
        UserState (Optional[PlexUserState]): The user state of the media container.
        _catchall (dict): A catch-all field for any additional attributes.
    """

    identifier: Optional[str] = None
    size: Optional[int] = None
    UserState: Optional[List[PlexUserState]] = None
    _catchall: dict = field(default_factory=dict)

