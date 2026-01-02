import requests


class DownloadClient:
    """A client to download files URLs with."""

    def __init__(self):
        """Initialize the DownloadClient object."""
        pass

    def get(self, url: str) -> bytes:
        """Download the subtitle referenced by url.

        Args:
            url: The url of the subtitle to download.

        Returns:
            The subtitles data in bytes.
        """
        download_remote_file = requests.get(url)

        return download_remote_file.content
