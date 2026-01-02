from pathlib import Path


class PlexFolder:
    def __init__(self, root: Path, title: str, year: int):
        self.root = root
        self.title = title
        self.year = year
    
    def path_from_root(self, suffix: Path) -> Path:
        return self.root / Path(self.base_name) / suffix

    @property
    def base_name(self) -> str:
        return f"{self.title} ({self.year})"
