from dataclasses import dataclass, field
from typing import List, Optional
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Uploader:
    uploader_id: Optional[int] = None
    name: Optional[str] = None
    rank: Optional[str] = None
    _catchall: dict = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FeatureDetails:
    feature_id: Optional[int] = None
    feature_type: Optional[str] = None
    year: Optional[int] = None
    title: Optional[str] = None
    movie_name: Optional[str] = None
    imdb_id: Optional[int] = None
    tmdb_id: Optional[int] = None
    _catchall: dict = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RelatedLinks:
    label: Optional[str] = None
    url: Optional[str] = None
    img_url: Optional[str] = None
    _catchall: dict = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Files:
    file_id: Optional[int] = None
    cd_number: Optional[int] = None
    file_name: Optional[str] = None
    _catchall: dict = field(default_factory=dict)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Attributes:
    subtitle_id: Optional[str] = None
    language: Optional[str] = None
    download_count: Optional[int] = None
    new_download_count: Optional[int] = None
    hearing_impaired: Optional[bool] = None
    hd: Optional[bool] = None
    fps: Optional[float] = None
    votes: Optional[int] = None
    ratings: Optional[float] = None
    from_trusted: Optional[bool] = None
    foreign_parts_only: Optional[bool] = None
    upload_date: Optional[str] = None
    ai_translated: Optional[bool] = None
    nb_cd: Optional[int] = None
    machine_translated: Optional[bool] = None
    release: Optional[str] = None
    comments: Optional[str] = None
    legacy_subtitle_id: Optional[int] = None
    legacy_uploader_id: Optional[int] = None
    uploader: Optional[Uploader] = None
    feature_details: Optional[FeatureDetails] = None
    url: Optional[str] = None
    related_links: Optional[List[RelatedLinks]] = None
    files: Optional[List[Files]] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.uploader, dict):
            self.uploader = Uploader(**self.uploader)
        if isinstance(self.feature_details, dict):
            self.feature_details = FeatureDetails(**self.feature_details)
        if isinstance(self.related_links, list):
            self.related_links = [RelatedLinks(**rl) if isinstance(rl, dict) else rl for rl in self.related_links]
        if isinstance(self.files, list):
            self.files = [Files(**f) if isinstance(f, dict) else f for f in self.files]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Data:
    id: Optional[str] = None
    type: Optional[str] = None
    attributes: Optional[Attributes] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.attributes, dict):
            self.attributes = Attributes(**self.attributes)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SubtitleData:
    total_pages: Optional[int] = None
    total_count: Optional[int] = None
    per_page: Optional[int] = None
    page: Optional[int] = None
    data: Optional[List[Data]] = None
    _catchall: dict = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.data, list):
            self.data = [Data(**d) if isinstance(d, dict) else d for d in self.data]
