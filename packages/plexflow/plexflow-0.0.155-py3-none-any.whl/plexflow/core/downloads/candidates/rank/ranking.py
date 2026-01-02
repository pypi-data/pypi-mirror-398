from plexflow.core.downloads.candidates.download_candidate import DownloadCandidate
from typing import List
from plexflow.core.downloads.candidates.rank.utils import rank_candidate

class RankedCandidate:
    def __init__(self, rank: float, candidate: DownloadCandidate):
        self.rank: float = rank
        self.candidate: DownloadCandidate = candidate

class Ranked:
    def __init__(self):
        self.ranked = {
            'native': {
                'nl': [],
                'en': []
            },
            'encoder': {
                'nl': [],
                'en': []
            },
            'nosub': [] 
        }
    
    def append_native(self, candidate: DownloadCandidate, rank: float, language: str):
        self.ranked['native'][language].append(RankedCandidate(rank, candidate))

    def append_encoder(self, candidate: DownloadCandidate, rank: float, language: str):
        self.ranked['encoder'][language].append(RankedCandidate(rank, candidate))

    def append_nosub(self, candidate: DownloadCandidate, rank: float):
        self.ranked['nosub'].append(RankedCandidate(rank, candidate))

    def native_candidates(self, language: str, tv_mode: bool = False):
        return sorted(self.ranked['native'][language], key=lambda rc: rc.rank if not tv_mode else rc.candidate.max_seeds, reverse=True)

    def encoder_candidates(self, language: str, tv_mode: bool = False):
        return sorted(self.ranked['encoder'][language], key=lambda rc: rc.rank if not tv_mode else rc.candidate.max_seeds, reverse=True)

    def nosub_candidates(self, tv_mode: bool = False):
        return sorted(self.ranked['nosub'], key=lambda rc: rc.rank if not tv_mode else rc.candidate.max_seeds, reverse=True)


def rank_candidates(candidates: List[DownloadCandidate]):
    ranked = Ranked()

    for candidate in candidates:
        seeds = candidate.max_seeds
        size = candidate.max_size_bytes

        rank = rank_candidate(seeds, size)

        if candidate.has_native_dutch_subtitles:
            # native dutch
            ranked.append_native(candidate=candidate, rank=rank, language='nl')
        elif candidate.has_native_english_subtitles:
            # native english
            ranked.append_native(candidate=candidate, rank=rank, language='en')
        elif candidate.has_dutch_subtitles:
            # encoder dutch
            ranked.append_encoder(candidate=candidate, rank=rank, language='nl')
        elif candidate.has_english_subtitles:
            # encoder english
            ranked.append_encoder(candidate=candidate, rank=rank, language='en')
        else:
            ranked.append_nosub(candidate=candidate, rank=rank)
    
    return ranked
