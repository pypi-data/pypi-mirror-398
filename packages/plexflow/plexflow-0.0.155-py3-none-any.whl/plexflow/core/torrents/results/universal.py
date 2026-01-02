from typing import List, Optional
from plexflow.core.subtitles.results.subtitle import Subtitle
from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode
from collections import defaultdict

from typing import List, Optional, Set

class UniversalTorrent:
    """
    Represents a universal torrent that contains multiple torrents with the same hash.

    Attributes:
        torrents (List[Torrent]): The list of torrents contained in the universal torrent.
    """

    def __init__(self, torrents: List[Torrent]):
        """
        Initializes a new instance of the UniversalTorrent class.

        Args:
            torrents (List[Torrent]): The list of torrents to be included in the universal torrent.

        Raises:
            ValueError: If the torrents have different hashes.
        """
        hashes = {t.hash for t in torrents}
        if len(hashes) > 1:
            raise ValueError("All torrents should have the same hash")
        self.torrents = torrents

    @property
    def imdb_code(self) -> IMDbCode:
        """
        Gets the IMDb code of the universal torrent.

        Returns:
            IMDbCode: The IMDb code of the universal torrent.
        """
        return self.torrents[0].imdb_code

    @property
    def is_season_pack(self) -> bool:
        """
        Checks if the universal torrent is a season pack.

        Returns:
            bool: True if the universal torrent is a season pack, False otherwise.
        """
        return any(t.has_multiple_episodes for t in self.torrents)

    @property
    def season(self) -> Optional[int]:
        """
        Gets the season number of the universal torrent.

        Returns:
            Optional[int]: The season number of the universal torrent, or None if not available.
        """
        for t in self.torrents:
            if isinstance(t.season, int):
                return t.season
        return None

    @property
    def episode(self) -> Optional[int]:
        """
        Gets the episode number of the universal torrent.

        Returns:
            Optional[int]: The episode number of the universal torrent, or None if not available.
        """
        for t in self.torrents:
            if isinstance(t.episode, int):
                return t.episode
        return None

    @property
    def max_peers(self) -> int:
        """
        Gets the maximum number of peers among all torrents in the universal torrent.

        Returns:
            int: The maximum number of peers.
        """
        return max(t.peers for t in self.torrents)

    @property
    def max_seeds(self) -> int:
        """
        Gets the maximum number of seeds among all torrents in the universal torrent.

        Returns:
            int: The maximum number of seeds.
        """
        return max(t.seeds for t in self.torrents)

    @property
    def min_seeds(self) -> int:
        """
        Gets the minimum number of seeds among all torrents in the universal torrent.

        Returns:
            int: The minimum number of seeds.
        """
        return min(t.seeds for t in self.torrents)

    @property
    def min_peers(self) -> int:
        """
        Gets the minimum number of peers among all torrents in the universal torrent.

        Returns:
            int: The minimum number of peers.
        """
        return min(t.peers for t in self.torrents)

    @property
    def sources(self) -> Set:
        """
        Gets the set of sources of the universal torrent.

        Returns:
            set: The set of sources.
        """
        return {t.source for t in self.torrents}

    @property
    def max_size_bytes(self) -> int:
        """
        Gets the maximum size in bytes among all torrents in the universal torrent.

        Returns:
            int: The maximum size in bytes.
        """
        return max(t.size_bytes for t in self.torrents)

    @property
    def min_size_bytes(self) -> int:
        """
        Gets the minimum size in bytes among all torrents in the universal torrent.

        Returns:
            int: The minimum size in bytes.
        """
        return min(t.size_bytes for t in self.torrents)

    @property
    def has_native_subtitles(self) -> bool:
        """
        Checks if the universal torrent has native subtitles.

        Returns:
            bool: True if the universal torrent has native subtitles, False otherwise.
        """
        return any(t.has_native_subtitles for t in self.torrents)

    @property
    def has_native_dutch_subtitles(self) -> bool:
        """
        Checks if the universal torrent has native Dutch subtitles.

        Returns:
            bool: True if the universal torrent has native Dutch subtitles, False otherwise.
        """
        return any(t.has_native_dutch_subtitles for t in self.torrents)

    @property
    def has_native_english_subtitles(self) -> bool:
        """
        Checks if the universal torrent has native English subtitles.

        Returns:
            bool: True if the universal torrent has native English subtitles, False otherwise.
        """
        return any(t.has_native_english_subtitles for t in self.torrents)

    def is_compatible_with(self, s: Subtitle) -> bool:
        """
        Checks if the universal torrent is compatible with a given subtitle.

        Args:
            s (Subtitle): The subtitle to check compatibility with.

        Returns:
            bool: True if the universal torrent is compatible with the subtitle, False otherwise.
        """
        torrent_parsed_release_names = [t.parsed_release_name for t in self.torrents]
        subtitle_parsed_release_name = s.parsed_release_name

        if any(s.release_name.lower().strip() == t.release_name.lower().strip() for t in self.torrents):
            return True
        elif any(subtitle_parsed_release_name.get('encoder', 'NO_ENCODER_SUBTITLE').strip().lower() == parsed_release_name.get('encoder', 'NO_ENCODER_TORRENT').strip().lower() for parsed_release_name in torrent_parsed_release_names):
            return True
        elif any((subtitle_parsed_release_name.get('encoder', 'NO_ENCODER_SUBTITLE').strip().lower() in parsed_release_name.get('encoder', 'NO_ENCODER_TORRENT').strip().lower() 
                  or parsed_release_name.get('encoder', 'NO_ENCODER_TORRENT').strip().lower() in subtitle_parsed_release_name.get('encoder', 'NO_ENCODER_SUBTITLE').strip().lower()) 
                  for parsed_release_name in torrent_parsed_release_names):
            return True
        # check for YTS
        elif 'yts' in s.release_name.strip().lower() and any('yts' in t.release_name.lower().strip() for t in self.torrents):
            return True

        return False

    def __eq__(self, other):
        """
        Checks if the universal torrent is equal to another object.

        Args:
            other: The object to compare with.

        Returns:
            bool: True if the universal torrent is equal to the other object, False otherwise.
        """
        if not isinstance(other, UniversalTorrent):
            return NotImplemented
        return self.torrents[0].hash == other.torrents[0].hash

    def __str__(self):
        """
        Returns a string representation of the universal torrent.

        Returns:
            str: The string representation of the universal torrent.
        """
        return f"UniversalTorrent({self.torrents[0].hash})"

    def __repr__(self):
        """
        Returns a string representation of the universal torrent.

        Returns:
            str: The string representation of the universal torrent.
        """
        return self.__str__()
