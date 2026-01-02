from plexflow.core.subtitles.providers.oss.utils.responses import Subtitle
from datetime import datetime
from plexflow.utils.imdb.imdb_codes import IMDbCode
import PTN

class OSSSubtitle(Subtitle):
    def __init__(self, subtitle: Subtitle):
        self.subtitle = subtitle
        self.src = "oss"
    
    @property
    def release_name(self) -> str:
        return self.subtitle.release
    
    @property
    def parsed_release_name(self) -> str:
        return PTN.parse(self.release_name)

    @property
    def uploader(self) -> str:
        return self.subtitle.uploader_name
    
    @property
    def date(self) -> datetime:
        return datetime.strptime(self.subtitle.upload_date, "%Y-%m-%dT%H:%M:%SZ")
    
    @property
    def imdb_code(self) -> IMDbCode:
        return IMDbCode(str(self.subtitle.imdb_id))
    
    @property
    def subtitle_id(self) -> str:
        return self.subtitle.id

    @property
    def language(self):
        return self.subtitle.language