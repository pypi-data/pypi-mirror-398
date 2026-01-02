from typing import Iterable, List
from plexflow.core.torrents.results.universal import UniversalTorrent
from plexflow.core.subtitles.utils.plex_external_subtitle import PlexExternalSubtitle
from plexflow.core.downloads.candidates.download_candidate import DownloadCandidate

def create_download_candidates(torrents: Iterable[UniversalTorrent], subtitles: Iterable[PlexExternalSubtitle]) -> List[DownloadCandidate]:
    """
    This function creates a list of DownloadCandidate objects from an iterable of UniversalTorrent and an iterable of PlexExternalSubtitle.
    All subtitles that are compatible with a torrent will become together a DownloadCandidate.

    Parameters:
    torrents (Iterable[UniversalTorrent]): An iterable of UniversalTorrent objects.
    subtitles (Iterable[PlexExternalSubtitle]): An iterable of PlexExternalSubtitle objects.

    Returns:
    List[DownloadCandidate]: A list of DownloadCandidate objects.

    Raises:
    ValueError: If either torrents or subtitles is not an iterable.
    """

    # Check if inputs are iterables
    if not isinstance(torrents, Iterable):
        raise ValueError("torrents should be an iterable of UniversalTorrent objects")
    if not isinstance(subtitles, Iterable):
        raise ValueError("subtitles should be an iterable of PlexExternalSubtitle objects")

    download_candidates = []

    for torrent in torrents:
        # Check if torrent is an instance of UniversalTorrent
        if not isinstance(torrent, UniversalTorrent):
            raise ValueError("Each torrent should be an instance of UniversalTorrent")

        compatible_subtitles = [subtitle for subtitle in subtitles if torrent.is_compatible_with(subtitle.oss_subtitle)]
        download_candidate = DownloadCandidate(torrent, compatible_subtitles)
        download_candidates.append(download_candidate)

    return download_candidates
