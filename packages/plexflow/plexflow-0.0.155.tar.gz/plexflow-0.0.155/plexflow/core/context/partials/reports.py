from plexflow.core.context.partial_context import PartialContext
from plexflow.utils.torrent.analyze import TorrentReport
from typing import List

class TorrentAnalysisReports(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @property
    def sources(self) -> list[str]:
        keys = self.get_keys("analysis/torrent/reports/*")
        # extract the source from the key
        return [key.split("/")[-1] for key in keys]

    def from_source(self, source: str) -> List[TorrentReport]:
        return self.get(f"analysis/torrent/reports/{source}")

    def update(self, reports: List[TorrentReport]):
        if len(reports) == 0:
            return
        source = next(iter(reports)).source
        self.set(f"analysis/torrent/reports/{source}", reports)
