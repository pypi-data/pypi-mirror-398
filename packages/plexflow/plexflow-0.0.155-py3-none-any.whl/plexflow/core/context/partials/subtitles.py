from plexflow.core.context.partial_context import PartialContext
from plexflow.core.subtitles.utils.plex_external_subtitle import PlexExternalSubtitle
from typing import List

class Subtitles(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def all(self) -> List[PlexExternalSubtitle]:
        return self.get("subtitles/oss")

    def update(self, subtitles: List[PlexExternalSubtitle]):
        if len(subtitles) == 0:
            return
        self.set("subtitles/oss", subtitles)
