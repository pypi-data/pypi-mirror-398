from plexflow.core.plex.library.folders.assets.plex_asset import PlexAsset
from pathlib import Path

class PlexVideoAsset(PlexAsset):
    def __init__(self, path, root, title, year, season: int = None, episode: int = None):
        super().__init__(path, root, title, year)
        self.season = season
        self.episode = episode

    @property
    def target_path(self) -> Path:
        if not self.season and not self.episode:
            return self.root / Path(f"{self.title} ({self.year})" + self.ext)
        else:
            return self.root / Path(f"S{self.season:02d}E{self.episode:02d}" + self.ext)
