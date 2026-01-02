from plexflow.core.context.partial_context import PartialContext
from datetime import datetime as dt
from plexflow.core.torrents.results.torrent import Torrent
from typing import List

class Torrents(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @property
    def sources(self) -> list[str]:
        keys = self.get_keys("torrents/*")
        # extract the source from the key
        return [key.split("/")[-1] for key in keys]

    def from_source(self, source: str) -> List[Torrent]:
        return self.get(f"torrents/{source}")

    def update(self, torrents: Torrent):
        if len(torrents) == 0:
            return
        source = next(iter(torrents)).source
        self.set(f"torrents/{source}", torrents)

    def update_subtitled(self, torrents: List[Torrent]):
        if len(torrents) == 0:
            return
        source = next(iter(torrents)).source
        self.set(f"subtitled/torrents/{source}", torrents)

    def from_subtitled_source(self, source: str) -> List[Torrent]:
        return self.get(f"subtitled/torrents/{source}")

