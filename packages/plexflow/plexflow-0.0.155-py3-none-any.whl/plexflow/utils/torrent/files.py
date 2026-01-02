from pydantic import BaseModel
from plexflow.utils.strings.filesize import parse_size
from pathlib import Path
from typing import Optional

class TorrentFile(BaseModel):
    """
    A model representing a torrent file.

    Attributes:
        name (Optional[str]): The name of the torrent file.
        size (Optional[str]): The size of the torrent file as a string.
    """
    name: Optional[str]
    size: Optional[str]
    
    @property
    def size_bytes(self) -> Optional[int]:
        """
        Get the size of the torrent file in bytes.

        Returns:
            Optional[int]: The size in bytes, or None if the size is not available.
        """
        return next(iter(parse_size(self.size)), None) if self.size else None

    @property
    def size_human(self) -> Optional[str]:
        """
        Get the human-readable size of the torrent file.

        Returns:
            Optional[str]: The human-readable size, or None if the size is not available.
        """
        return self.size

    @property
    def extension(self) -> Optional[str]:
        """
        Get the file extension of the torrent file.

        Returns:
            Optional[str]: The file extension, or None if the name is not available.
        """
        return Path(self.name).suffix.lstrip('.') if self.name else None

    def __str__(self) -> str:
        """
        Get a string representation of the torrent file.

        Returns:
            str: A string representation of the torrent file.
        """
        return f"{self.name} [({self.size_human})][{self.extension}][{self.size_bytes} bytes]"

    def __repr__(self) -> str:
        """
        Get a string representation of the torrent file for debugging.

        Returns:
            str: A string representation of the torrent file.
        """
        return self.__str__()

class TorrentSubtitle(BaseModel):
    """
    A model representing a torrent subtitle.

    Attributes:
        language (Optional[str]): The language of the subtitle.
        name (Optional[str]): The name of the subtitle file.
    """
    language: Optional[str]
    name: Optional[str]
    
    def __str__(self) -> str:
        return f"{self.language} - {self.name}"
    
    def __repr__(self) -> str:
        return self.__str__()
