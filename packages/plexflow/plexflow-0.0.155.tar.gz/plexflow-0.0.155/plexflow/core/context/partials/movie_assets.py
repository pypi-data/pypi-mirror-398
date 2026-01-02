from plexflow.core.context.partial_context import PartialContext
from typing import List, Tuple
from qbittorrentapi.torrents import TorrentDictionary
from plexflow.core.subtitles.utils.plex_internal_subtitle import PlexInternalSubtitle
from plexflow.core.subtitles.utils.plex_external_subtitle import PlexExternalSubtitle

class MovieAssets(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def all(self) -> List[TorrentDictionary]:
        return self.get("download/completed")

    def movie_path(self) -> str:
        return self.get("assets/movie/path")

    def internal_subtitles(self) -> List[PlexInternalSubtitle]:
        return self.get("assets/subtitles/internal")
    
    def external_subtitles(self) -> List[PlexExternalSubtitle]:
        return self.get("assets/subtitles/external")

    def subtitle_paths(self) -> List[str]:
        return self.get("assets/subtitle/path")

    def embedded_subtitles(self) -> List[Tuple[int,str]]:
        return self.get("assets/embedded_subtitles")

    def languaged_subtitle_paths(self) -> List[Tuple[str, str]]:
        return self.get("assets/languaged_subtitle/path")

    def update_movie_path(self, path: str):
        self.set("assets/movie/path", path)

    def update_subtitle_paths(self, paths: List[str]):
        self.set("assets/subtitle/path", paths)

    def update_internal_subtitles(self, subtitles: List[PlexInternalSubtitle]):
        self.set("assets/subtitles/internal", subtitles)

    def update_external_subtitles(self, subtitles: List[PlexExternalSubtitle]):
        self.set("assets/subtitles/external", subtitles)

    def update_embedded_subtitles(self, subtitles: List[Tuple[int, str]]):
        self.set("assets/embedded_subtitles", subtitles)

    def update_languaged_subtitle_paths(self, paths: List[Tuple[str,str]]):
        self.set("assets/languaged_subtitle/path", paths)

