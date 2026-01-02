from abc import ABC, abstractmethod
from datetime import datetime
import PTN
from typing import List, Union
from plexflow.utils.imdb.imdb_codes import IMDbCode

class Torrent(ABC):
    """
    This is an abstract base class that represents a Torrent.
    Any class that inherits from this must implement all the properties.
    """
    @property
    @abstractmethod
    def seeds(self) -> int:
        """
        This property represents the number of seeds for the torrent.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    @abstractmethod
    def peers(self) -> int:
        """
        This property represents the number of peers for the torrent.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    @abstractmethod
    def release_name(self) -> str:
        """
        This property represents the release name of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    @abstractmethod
    def size_bytes(self) -> int:
        """
        This property represents the size of the torrent in bytes.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    @abstractmethod
    def magnet(self) -> str:
        """
        This property represents the magnet link of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    @abstractmethod
    def hash(self) -> str:
        """
        This property represents the hash of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    def uploader(self) -> str:
        """
        This property represents the uploader of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        return self.source
    
    @property
    @abstractmethod
    def date(self) -> datetime:
        """
        This property represents the date of the torrent upload.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    @abstractmethod
    def imdb_code(self) -> IMDbCode:
        """
        This property represents the IMDB code of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        pass
    
    @property
    def source(self) -> str:
        """
        This property represents the source of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        return self.src
    
    @property
    def torrent_id(self) -> str:
        """
        This property represents the id of the torrent.
        It must be implemented by any class that inherits from this class.
        """
        return self.source + "_" + self.hash

    @property
    def parsed_release_name(self) -> dict:
        return PTN.parse(self.release_name)
    
    @property
    def encoder_name(self) -> str:
        parts = self.parsed_release_name
        return parts.get("encoder")

    @property
    def season(self) -> Union[int, List[int]]:
        parts = self.parsed_release_name
        return parts.get("season")
    
    @property
    def episode(self) -> Union[int, List[int]]:
        parts = self.parsed_release_name
        return parts.get("episode")

    @property
    def has_multiple_episodes(self):
        tmp = self.episode
        return isinstance(tmp, list) and len(tmp) > 1

    @property
    def has_multiple_seasons(self):
        tmp = self.season
        return isinstance(tmp, list) and len(tmp) > 1
        
    @property
    def title(self) -> str:
        parts = self.parsed_release_name
        return parts.get("title")
        
    @property
    def year(self) -> int:
        parts = self.parsed_release_name
        return parts.get("year")

    @property
    def quality(self) -> str:
        parts = self.parsed_release_name
        return parts.get("quality")

    @property
    def has_native_dutch_subtitles(self):
        return len(self._native_dutch_subtitles) > 0

    @property
    def has_native_english_subtitles(self):
        return len(self._native_english_subtitles) > 0

    def add_native_dutch_subtitle(self, name: str):
        self._native_dutch_subtitles.append(name)

    def add_native_english_subtitle(self, name: str):
        self._native_english_subtitles.append(name)

    @property
    def is_bad_quality(self):
        parsed_title = self.parsed_release_name
        bad_qualities = ['CAM', 'HDCAM', 'TS', 'HDTS', 'TELESYNC', 
                         'PDVD', 'PREDVDRIP', 'WP', 'WORKPRINT', 'TC', 
                         'HDTC', 'TELECINE', 'PPV', 'PPVRIP', 'SCR', 'SCREENER', 
                         'DVDSCR', 'DVDSCREENER', 'BDSCR', 'WEBSCREENER', 'DDC', 
                         'R5', 'R5.LINE', 'R5.AC3.5.1.HQ']
        return parsed_title.get('quality', '').upper() in bad_qualities

    @property
    def url(self) -> str:
        return None
