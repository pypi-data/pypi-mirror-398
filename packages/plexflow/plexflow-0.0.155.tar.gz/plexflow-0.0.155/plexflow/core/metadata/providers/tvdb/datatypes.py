from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json, Undefined
import json

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Alias:
    language: Optional[str] = None
    name: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Artwork:
    height: Optional[int] = None
    id: Optional[int] = None
    image: Optional[str] = None
    includesText: Optional[bool] = None
    language: Optional[str] = None
    score: Optional[int] = None
    thumbnail: Optional[str] = None
    type: Optional[int] = None
    width: Optional[int] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Award:
    id: Optional[int] = None
    name: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Character:
    aliases: Optional[List[Alias]] = None
    episode: Optional[dict] = None
    episodeId: Optional[int] = None
    id: Optional[int] = None
    image: Optional[str] = None
    isFeatured: Optional[bool] = None
    movieId: Optional[int] = None
    movie: Optional[dict] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    overviewTranslations: Optional[List[str]] = None
    peopleId: Optional[int] = None
    personImgURL: Optional[str] = None
    peopleType: Optional[str] = None
    seriesId: Optional[int] = None
    series: Optional[dict] = None
    sort: Optional[int] = None
    tagOptions: Optional[List[dict]] = None
    type: Optional[int] = None
    url: Optional[str] = None
    personName: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Company:
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
    parentCompany: Optional[dict] = None
    tagOptions: Optional[List[dict]] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ContentRating:
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    contentType: Optional[str] = None
    order: Optional[int] = None
    fullName: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FirstRelease:
    country: Optional[str] = None
    date: Optional[str] = None
    detail: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Genre:
    id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Inspiration:
    id: Optional[int] = None
    type: Optional[str] = None
    type_name: Optional[str] = None
    url: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ListData:
    aliases: Optional[List[Alias]] = None
    id: Optional[int] = None
    image: Optional[str] = None
    imageIsFallback: Optional[bool] = None
    isOfficial: Optional[bool] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    overview: Optional[str] = None
    overviewTranslations: Optional[List[str]] = None
    remoteIds: Optional[List[dict]] = None
    tags: Optional[List[dict]] = None
    score: Optional[int] = None
    url: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ProductionCountry:
    id: Optional[int] = None
    country: Optional[str] = None
    name: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Release:
    country: Optional[str] = None
    date: Optional[str] = None
    detail: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RemoteId:
    id: Optional[str] = None
    type: Optional[int] = None
    sourceName: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Status:
    id: Optional[int] = None
    keepUpdated: Optional[bool] = None
    name: Optional[str] = None
    recordType: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Studio:
    id: Optional[int] = None
    name: Optional[str] = None
    parentStudio: Optional[int] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TagOption:
    helpText: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    tag: Optional[int] = None
    tagName: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Trailer:
    id: Optional[int] = None
    language: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    runtime: Optional[int] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

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
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SubtitleLanguage:
    language: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TvdbMovie:
    aliases: Optional[List[Alias]] = None
    artworks: Optional[List[Artwork]] = None
    audioLanguages: Optional[List[str]] = None
    awards: Optional[List[Award]] = None
    boxOffice: Optional[str] = None
    boxOfficeUS: Optional[str] = None
    budget: Optional[str] = None
    characters: Optional[List[Character]] = None
    companies: Optional[dict] = None
    contentRatings: Optional[List[ContentRating]] = None
    first_release: Optional[FirstRelease] = None
    genres: Optional[List[Genre]] = None
    id: Optional[int] = None
    image: Optional[str] = None
    inspirations: Optional[List[Inspiration]] = None
    lastUpdated: Optional[str] = None
    lists: Optional[List[ListData]] = None
    name: Optional[str] = None
    nameTranslations: Optional[List[str]] = None
    originalCountry: Optional[str] = None
    originalLanguage: Optional[str] = None
    overviewTranslations: Optional[List[str]] = None
    production_countries: Optional[List[ProductionCountry]] = None
    releases: Optional[List[Release]] = None
    remoteIds: Optional[List[RemoteId]] = None
    runtime: Optional[int] = None
    score: Optional[int] = None
    slug: Optional[str] = None
    spoken_languages: Optional[List[str]] = None
    status: Optional[Status] = None
    studios: Optional[List[Studio]] = None
    subtitleLanguages: Optional[List[SubtitleLanguage]] = None
    tagOptions: Optional[List[TagOption]] = None
    trailers: Optional[List[Trailer]] = None
    translations: Optional[dict] = None
    year: Optional[str] = None
    _catchall: Dict[str, str] = field(default_factory=dict)


def movie_from_json(json_str: str) -> TvdbMovie:
    return TvdbMovie.from_json(json_str)

def show_from_json():
    pass
