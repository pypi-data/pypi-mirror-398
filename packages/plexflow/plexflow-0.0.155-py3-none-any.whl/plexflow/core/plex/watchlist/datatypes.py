from dataclasses import dataclass, field
from typing import Optional, List
import json
from dataclasses_json import dataclass_json, Undefined, CatchAll

@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class PlexImage:
    """
    Represents an image with optional alt text, type, and URL.

    Attributes:
        alt (Optional[str]): The alt text of the image.
        type (Optional[str]): The type of the image.
        url (Optional[str]): The URL of the image.
    """
    alt: Optional[str] = field(default=None)
    type: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)
    _catch_all: CatchAll = field(default_factory=dict)

@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class PlexMetadata:
    """
    Represents the metadata of a media item.

    Attributes:
        Image (Optional[List[Image]]): A list of Image objects associated with the media item.
        addedAt (Optional[int]): The timestamp when the media item was added.
        art (Optional[str]): The URL of the artwork of the media item.
        audienceRating (Optional[float]): The audience rating of the media item.
        audienceRatingImage (Optional[str]): The URL of the audience rating image.
        banner (Optional[str]): The URL of the banner image.
        contentRating (Optional[str]): The content rating of the media item.
        duration (Optional[int]): The duration of the media item in seconds.
        guid (Optional[str]): The globally unique identifier of the media item.
        imdbRatingCount (Optional[int]): The number of IMDb ratings.
        key (Optional[str]): The key of the media item.
        originallyAvailableAt (Optional[str]): The original release date of the media item.
        publicPagesURL (Optional[str]): The URL of the public pages.
        rating (Optional[float]): The rating of the media item.
        ratingImage (Optional[str]): The URL of the rating image.
        ratingKey (Optional[str]): The rating key of the media item.
        slug (Optional[str]): The slug of the media item.
        studio (Optional[str]): The studio that produced the media item.
        tagline (Optional[str]): The tagline of the media item.
        thumb (Optional[str]): The URL of the thumbnail image.
        title (Optional[str]): The title of the media item.
        type (Optional[str]): The type of the media item.
        userState (Optional[bool]): The user state of the media item.
        year (Optional[int]): The release year of the media item.
    """

    Image: Optional[List[PlexImage]] = field(default_factory=list)
    addedAt: Optional[int] = None
    art: Optional[str] = None
    audienceRating: Optional[float] = None
    audienceRatingImage: Optional[str] = None
    banner: Optional[str] = None
    contentRating: Optional[str] = None
    duration: Optional[int] = None
    guid: Optional[str] = None
    imdbRatingCount: Optional[int] = None
    key: Optional[str] = None
    originallyAvailableAt: Optional[str] = None
    publicPagesURL: Optional[str] = None
    rating: Optional[float] = None
    ratingImage: Optional[str] = None
    ratingKey: Optional[str] = None
    slug: Optional[str] = None
    studio: Optional[str] = None
    tagline: Optional[str] = None
    thumb: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    userState: Optional[bool] = None
    year: Optional[int] = None
    _catch_all: CatchAll = field(default_factory=dict)
    
    def __post_init__(self):
        self.Image = [PlexImage(**img) if isinstance(img, dict) else img for img in self.Image]
    
    @property
    def is_movie(self):
        return self.type == "movie"

    @property
    def is_show(self):
        return self.type == "show"

@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class MediaContainer:
    """
    Represents a media container with metadata and other properties.

    Attributes:
        Metadata (Optional[List[PlexMetadata]]): A list of Metadata objects associated with the media container.
        identifier (Optional[str]): The identifier of the media container.
        librarySectionID (Optional[str]): The ID of the library section.
        librarySectionTitle (Optional[str]): The title of the library section.
        offset (Optional[int]): The offset of the media container.
        size (Optional[int]): The size of the media container.
        totalSize (Optional[int]): The total size of the media container.
    """

    Metadata: Optional[List[PlexMetadata]] = field(default_factory=list)
    identifier: Optional[str] = None
    librarySectionID: Optional[str] = None
    librarySectionTitle: Optional[str] = None
    offset: Optional[int] = None
    size: Optional[int] = None
    totalSize: Optional[int] = None
    _catch_all: CatchAll = field(default_factory=dict)
    
    def __post_init__(self):
        self.Metadata = [PlexMetadata(**meta) if isinstance(meta, dict) else meta for meta in self.Metadata]

def from_json(json_str: str) -> MediaContainer:
    try:
        return MediaContainer(**json.loads(json_str).get("MediaContainer"))
    except json.JSONDecodeError as e:
        raise f"Error decoding JSON: {e}"
