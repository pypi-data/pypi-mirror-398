from datetime import datetime

class OpenSubtitlesException(Exception):
    """Custom exception class for the OpenSubtitles wrapper."""

    def __init__(self, message: str):
        """
        Initialize the custom exception.

        :param message: exception message.
        """
        self.message = message


class OpenSubtitlesDownloadQuotaReachedException(Exception):
    def __init__(self, message: str, reset_time: datetime):
        """
        Initialize the custom exception.

        :param message: exception message.
        """
        self.message = message
        self.reset_time = reset_time


class OpenSubtitlesFileException(Exception):
    """Custom exception class for files operations in OpenSubtitles wrapper."""

    def __init__(self, message: str):
        """
        Initialize the custom exception.

        :param message: exception message.
        """
        self.message = message
