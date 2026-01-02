from plexflow.core.context.partial_context import PartialContext
from datetime import datetime as dt
from plexflow.core.torrents.results.universal import UniversalTorrent
from typing import List

class UniversalTorrents(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def all(self) -> List[UniversalTorrent]:
        return self.get("universal/torrents")

    def update(self, torrents: List[UniversalTorrent]):
        if len(torrents) == 0:
            return
        self.set(f"universal/torrents", torrents)
