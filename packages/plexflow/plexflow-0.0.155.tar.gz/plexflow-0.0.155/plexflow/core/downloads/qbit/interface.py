import qbittorrentapi
from typing import List
from qbittorrentapi.torrents import TorrentDictionary

def list_torrents(torrent_hashes: List[str] = None, category: str = None, tag: str = None,  **kwargs) -> TorrentDictionary:
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
        return qbt_client.torrents.info(
            torrent_hashes=torrent_hashes,
            category=category,
            tag=tag,
        )

def force_start(torrent: TorrentDictionary, **kwargs):
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
        return qbt_client.torrents_setForceStart(enable=True, torrent_hashes=torrent.hash)

def remove(torrent: TorrentDictionary, hard: bool, **kwargs):
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
        return qbt_client.torrents_delete(delete_files=hard, torrent_hashes=torrent.hash)

def add_tags(torrent: TorrentDictionary, tags, **kwargs):
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
        return qbt_client.torrents_add_tags(tags=tags, torrent_hashes=torrent.hash)

def remove_tags(torrent: TorrentDictionary, tags, **kwargs):
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
        return qbt_client.torrents_remove_tags(tags=tags, torrent_hashes=torrent.hash)

def is_completed(torrent: TorrentDictionary) -> bool:
    return torrent.state in [
        "seeding",
        "completed",
        "uploading",
        "stalled_uploading",
        "stalledUP",
        "forcedUP",
    ]

def is_downloading(torrent: TorrentDictionary) -> bool:
    return torrent.state in [
        "downloading",
        # "stalled_downloading",
        "checking",
        # "stalledDL", 
        "forcedDL",
    ]

def is_errored(torrent: TorrentDictionary) -> bool:
    return torrent.state in [
        "errored",
    ]