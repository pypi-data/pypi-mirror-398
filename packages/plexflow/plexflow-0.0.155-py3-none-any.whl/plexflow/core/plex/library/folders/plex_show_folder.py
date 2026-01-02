import shutil as sh
import logging
from typing import List
from plexflow.core.plex.library.folders.plex_folder import PlexFolder
from plexflow.core.plex.library.folders.assets.plex_asset import PlexAsset
from plexflow.core.plex.library.folders.assets.plex_video_asset import PlexVideoAsset
from plexflow.core.plex.library.folders.assets.plex_subtitle_asset import PlexSubtitleAsset

class PlexShowFolder(PlexFolder):
    def __init__(self, root, title, year, season: int, episode: int):
        super().__init__(root, title, year)
        self.assets: List[PlexAsset] = []
        self.subtitle_index = None
        self.season = season
        self.episode = episode
    
    def add_video_path(self, path: str):
        video_asset = PlexVideoAsset(path, root=self.path_from_root(f"Season {self.season:02d}"), title=self.title, year=self.year, season=self.season, episode=self.episode)
        self.assets.append(video_asset)
    
    def add_subtitle_path(self, path: str, lang: str):
        subtitle_asset = PlexSubtitleAsset(path, root=self.path_from_root(f"Season {self.season:02d}"), title=self.title, year=self.year, lang=lang, index=self.subtitle_index, season=self.season, episode=self.episode)
        self.assets.append(subtitle_asset)
        self.subtitle_index = self.subtitle_index + 1 if self.subtitle_index else 1
    
    def create(self, dry_run: bool = False):
        for asset in self.assets:
            source = asset.source_path
            target = asset.target_path

            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)

            logging.info(f"moving {source} to {target}")
            
            if not dry_run:
                if isinstance(asset, PlexVideoAsset):
                    sh.move(src=str(source), dst=str(target))
                else:
                    sh.copyfile(src=str(source), dst=str(target))
