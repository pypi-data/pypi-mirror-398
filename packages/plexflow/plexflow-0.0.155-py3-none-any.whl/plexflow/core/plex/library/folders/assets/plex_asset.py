from pathlib import Path
import os


class PlexAsset:
    def __init__(self, path: str, root: Path, title: str, year: int):
        self.path = path
        self.root = root
        self.title = title
        self.year = year
    
    @property
    def ext(self) -> str:
        return os.path.splitext(self.path)[1]
    
    @property
    def source_path(self) -> Path:
        return Path(self.path)
    
    @property
    def target_path(self) -> Path:
        return self.root / Path(f"{self.title} ({self.year})" + self.ext)
