
from plexflow.core.subtitles.utils.plex_subtitle import PlexSubtitle

class PlexInternalSubtitle(PlexSubtitle):
    def __init__(self, path, name):
        super().__init__(path, name)