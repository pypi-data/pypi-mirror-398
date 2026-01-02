from plexflow.core.subtitles.providers.oss.oss_subtitle import OSSSubtitle
from plexflow.core.subtitles.utils.plex_subtitle import PlexSubtitle

class PlexExternalSubtitle(PlexSubtitle):
    def __init__(self, path, name, subtitle: OSSSubtitle):
        super().__init__(path, name)
        self.subtitle = subtitle
    
    @property
    def oss_subtitle(self) -> OSSSubtitle:
        return self.subtitle
