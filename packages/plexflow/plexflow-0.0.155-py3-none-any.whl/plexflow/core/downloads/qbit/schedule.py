import qbittorrentapi
from plexflow.core.downloads.candidates.download_candidate import DownloadCandidate
from typing import List


def schedule_download(magnet: str, category: str = None, tags: List[str] = (), save_path: str = None, **kwargs):
    # instantiate a Client using the appropriate WebUI configuration
    conn_info = dict(
        host=kwargs.get("qbit_host"),
        port=kwargs.get("qbit_port"),
        username=kwargs.get("qbit_username"),
        password=kwargs.get("qbit_password"),
    )
    qbt_client = qbittorrentapi.Client(**conn_info)

    # or use a context manager:
    with qbittorrentapi.Client(**conn_info) as qbt_client:
        if qbt_client.torrents_add(
            urls=magnet, 
            save_path=save_path,
            content_layout='Subfolder',
            tags=tags,
            category=category) != "Ok.":
            raise Exception("Failed to add torrent.")
