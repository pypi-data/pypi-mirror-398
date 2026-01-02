import math
from typing import List, Optional, Set
from plexflow.core.torrents.results.universal import UniversalTorrent
from plexflow.core.subtitles.utils.plex_external_subtitle import PlexExternalSubtitle
from plexflow.utils.imdb.imdb_codes import IMDbCode

class DownloadCandidate:
    """
    Represents a download candidate for a torrent with associated subtitles.
    """

    def __init__(self, torrent: UniversalTorrent, subtitles: List[PlexExternalSubtitle]):
        """
        Initializes a new instance of the DownloadCandidate class.

        Args:
            torrent (UniversalTorrent): The torrent associated with the download candidate.
            subtitles (List[Subtitle]): The list of subtitles associated with the download candidate.
        """
        self.torrent = torrent
        self.subtitles = subtitles

    @property
    def imdb_code(self) -> IMDbCode:
        """
        Get the IMDb code of the torrent.

        Returns:
            IMDbCode: The IMDb code of the torrent.
        """
        return self.torrent.imdb_code

    @property
    def is_season_pack(self) -> bool:
        """
        Check if the torrent is a season pack.

        Returns:
            bool: True if the torrent is a season pack, False otherwise.
        """
        return self.torrent.is_season_pack

    @property
    def season(self) -> Optional[int]:
        """
        Get the season number of the torrent.

        Returns:
            Optional[int]: The season number of the torrent, or None if not applicable.
        """
        return self.torrent.season

    @property
    def episode(self) -> Optional[int]:
        """
        Get the episode number of the torrent.

        Returns:
            Optional[int]: The episode number of the torrent, or None if not applicable.
        """
        return self.torrent.episode

    @property
    def max_peers(self) -> int:
        """
        Get the maximum number of peers for the torrent.

        Returns:
            int: The maximum number of peers for the torrent.
        """
        return self.torrent.max_peers

    @property
    def max_seeds(self) -> int:
        """
        Get the maximum number of seeds for the torrent.

        Returns:
            int: The maximum number of seeds for the torrent.
        """
        return self.torrent.max_seeds

    @property
    def min_seeds(self) -> int:
        """
        Get the minimum number of seeds for the torrent.

        Returns:
            int: The minimum number of seeds for the torrent.
        """
        return self.torrent.min_seeds

    @property
    def min_peers(self) -> int:
        """
        Get the minimum number of peers for the torrent.

        Returns:
            int: The minimum number of peers for the torrent.
        """
        return self.torrent.min_peers

    @property
    def sources(self) -> Set:
        """
        Get the set of sources for the torrent.

        Returns:
            Set: The set of sources for the torrent.
        """
        return self.torrent.sources

    @property
    def max_size_bytes(self) -> int:
        """
        Get the maximum size of the torrent in bytes.

        Returns:
            int: The maximum size of the torrent in bytes.
        """
        return self.torrent.max_size_bytes

    @property
    def min_size_bytes(self) -> int:
        """
        Get the minimum size of the torrent in bytes.

        Returns:
            int: The minimum size of the torrent in bytes.
        """
        return self.torrent.min_size_bytes

    @property
    def has_native_subtitles(self) -> bool:
        """
        Check if the torrent has native subtitles.

        Returns:
            bool: True if the torrent has native subtitles, False otherwise.
        """
        return self.torrent.has_native_subtitles

    @property
    def has_native_dutch_subtitles(self) -> bool:
        """
        Check if the torrent has native Dutch subtitles.

        Returns:
            bool: True if the torrent has native Dutch subtitles, False otherwise.
        """
        return self.torrent.has_native_dutch_subtitles

    @property
    def has_native_english_subtitles(self) -> bool:
        """
        Check if the torrent has native English subtitles.

        Returns:
            bool: True if the torrent has native English subtitles, False otherwise.
        """
        return self.torrent.has_native_english_subtitles

    @property
    def fitness(self) -> float:
        """
        Calculate the fitness score of the download candidate.

        Returns:
            float: The fitness score of the download candidate.
        """
        return self.max_seeds / max(math.sqrt(self.min_size_bytes), 1)

    @property
    def has_subtitles(self) -> bool:
        """
        Check if the download candidate has subtitles.

        Returns:
            bool: True if the download candidate has subtitles, False otherwise.
        """
        return any([
            self.has_native_subtitles,
            len(self.subtitles) > 0
        ])

    @property
    def magnets(self) -> List[str]:
        return [t.magnet for t in self.torrent.torrents]

    @property
    def has_dutch_subtitles(self) -> bool:
        """
        Check if the download candidate has Dutch subtitles.

        Returns:
            bool: True if the download candidate has Dutch subtitles, False otherwise.
        """
        return any([
            self.has_native_dutch_subtitles,
            any(s.oss_subtitle.language == "nl" for s in self.subtitles),
        ])

    @property
    def has_english_subtitles(self) -> bool:
        """
        Check if the download candidate has English subtitles.

        Returns:
            bool: True if the download candidate has English subtitles, False otherwise.
        """
        return any([
            self.has_native_english_subtitles,
            any(s.oss_subtitle.language == "en" for s in self.subtitles),
        ])
