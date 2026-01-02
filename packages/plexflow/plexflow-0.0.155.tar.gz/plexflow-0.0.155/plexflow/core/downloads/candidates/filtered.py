from plexflow.core.downloads.candidates.download_candidate import DownloadCandidate
from typing import List

class FilteredCandidates:
    """
    Represents a collection of filtered download candidates based on specific criteria.

    Args:
        imdb_id (str): The IMDb ID of the movie.
        year (int): The release year of the movie.
        titles (List[str]): A list of movie titles.
        candidates (List[DownloadCandidate]): A list of download candidates.

    Attributes:
        imdb_id (str): The IMDb ID of the movie.
        year (int): The release year of the movie.
        titles (List[str]): A list of movie titles.
        candidates (List[DownloadCandidate]): A list of download candidates.
    """

    def __init__(self, imdb_id: str, year: int, titles: List[str], candidates: List[DownloadCandidate]):
        self.imdb_id = imdb_id
        self.year = year
        self.titles = titles
        self.candidates = candidates

    def __iter__(self):
        """
        Returns an iterator that yields candidates from the `candidates` list
        if they match the criteria specified by the `_is_match` method.

        Yields:
            candidate: A candidate that matches the criteria.
        """
        return (candidate for candidate in self.candidates if self._is_match(candidate))

    def _is_match(self, candidate: DownloadCandidate) -> bool:
        """
        Checks if the given candidate is a match for the current filter.

        Args:
            candidate (DownloadCandidate): The candidate to check.

        Returns:
            bool: True if the candidate is a match, False otherwise.
        """
        if candidate.imdb_code == self.imdb_id:
            return True
        if candidate.year == self.year and candidate.title in self.titles:
            return True
        return False
