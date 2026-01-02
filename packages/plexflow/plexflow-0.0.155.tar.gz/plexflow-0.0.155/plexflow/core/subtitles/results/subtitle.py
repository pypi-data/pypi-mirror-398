from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Union
import PTN

class Subtitle(ABC):
    """
    Abstract base class for subtitle objects.
    """

    @property
    @abstractmethod
    def release_name(self) -> str:
        """
        Gets the release name of the subtitle.

        Returns:
            str: The release name of the subtitle.
        """
        pass

    @property
    def uploader(self) -> str:
        """
        Gets the uploader of the subtitle.

        Returns:
            str: The uploader of the subtitle.
        """
        return self.source

    @property
    @abstractmethod
    def date(self) -> datetime:
        """
        Gets the date of the subtitle.

        Returns:
            datetime: The date of the subtitle.
        """
        pass

    @property
    @abstractmethod
    def imdb_code(self) -> str:
        """
        Gets the IMDb code of the subtitle.

        Returns:
            str: The IMDb code of the subtitle.
        """
        pass

    @property
    def source(self) -> str:
        """
        Gets the source of the subtitle.

        Returns:
            str: The source of the subtitle.
        """
        return self.src

    @property
    @abstractmethod
    def language(self):
        """
        Gets the language of the subtitle.

        Returns:
            The language of the subtitle.
        """
        pass

    @property
    def subtitle_id(self) -> str:
        """
        Gets the subtitle ID.

        Returns:
            str: The subtitle ID.
        """
        return f"{self.source}_{self.hash}"

    @property
    def parsed_release_name(self) -> dict:
        """
        Parses the release name of the subtitle.

        Returns:
            dict: The parsed release name of the subtitle.
        """
        return PTN.parse(self.release_name)

    @property
    def encoder_name(self) -> str:
        """
        Gets the encoder name of the subtitle.

        Returns:
            str: The encoder name of the subtitle.
        """
        parts = self.parsed_release_name
        return parts.get("encoder")

    @property
    def season(self) -> Union[int, List[int]]:
        """
        Gets the season number of the subtitle.

        Returns:
            Union[int, List[int]]: The season number of the subtitle.
        """
        parts = self.parsed_release_name
        return parts.get("season")

    @property
    def episode(self) -> Union[int, List[int]]:
        """
        Gets the episode number of the subtitle.

        Returns:
            Union[int, List[int]]: The episode number of the subtitle.
        """
        parts = self.parsed_release_name
        return parts.get("episode")

    @property
    def has_multiple_episodes(self):
        """
        Checks if the subtitle has multiple episodes.

        Returns:
            bool: True if the subtitle has multiple episodes, False otherwise.
        """
        tmp = self.episode
        return isinstance(tmp, list) and len(tmp) > 1

    @property
    def has_multiple_seasons(self):
        """
        Checks if the subtitle has multiple seasons.

        Returns:
            bool: True if the subtitle has multiple seasons, False otherwise.
        """
        tmp = self.season
        return isinstance(tmp, list) and len(tmp) > 1

    @property
    def title(self) -> str:
        """
        Gets the title of the subtitle.

        Returns:
            str: The title of the subtitle.
        """
        parts = self.parsed_release_name
        return parts.get("title")

    @property
    def year(self) -> int:
        """
        Gets the year of the subtitle.

        Returns:
            int: The year of the subtitle.
        """
        parts = self.parsed_release_name
        return parts.get("year")
