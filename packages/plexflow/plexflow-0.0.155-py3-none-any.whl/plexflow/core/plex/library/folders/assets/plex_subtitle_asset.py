from pathlib import Path
from plexflow.core.plex.library.folders.assets.plex_asset import PlexAsset


class PlexSubtitleAsset(PlexAsset):
    def __init__(self, path: str, root: Path, title: str, year: int, lang: str, index: int = None, season: int = None, episode: int = None):
        super().__init__(path, root, title, year)
        self.lang = lang
        self.index = index
        self.season = season
        self.episode = episode

    @property
    def target_path(self) -> Path:
        if not self.season and not self.episode:
            return self.root / Path(f"{self.title} ({self.year}){'.' + str(self.index) if self.index else ''}.{self.lang}" + self.ext)
        else:
            return self.root / Path(f"S{self.season:02d}E{self.episode:02d}{'.' + str(self.index) if self.index else ''}.{self.lang}" + self.ext)
