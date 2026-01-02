from plexflow.core.context.partial_context import PartialContext
from plexflow.core.downloads.candidates.download_candidate import DownloadCandidate
from typing import List
from plexflow.core.downloads.candidates.rank.ranking import Ranked

class Candidates(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def all(self) -> List[DownloadCandidate]:
        return self.get("download/candidates")

    def update(self, candidates: List[DownloadCandidate]):
        if len(candidates) == 0:
            return
        self.set("download/candidates", candidates)

    def update_ranked(self, ranked_candidates: Ranked):
        self.set('download/ranked/candidates', ranked_candidates)
    
    def ranked(self) -> Ranked:
        return self.get('download/ranked/candidates')
    
    def update_selected(self, candidate: DownloadCandidate):
        self.set('download/selected', candidate)
    
    def selected(self) -> DownloadCandidate:
        return self.get('download/selected')