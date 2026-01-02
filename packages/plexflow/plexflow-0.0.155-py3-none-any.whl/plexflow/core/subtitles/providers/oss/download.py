from typing import List, Any
from contextlib import contextmanager, ExitStack
from plexflow.core.subtitles.providers.oss.unlimited_oss import OpenSubtitlesManager, Subtitle, OpenSubtitlesDownloadQuotaReachedException
from plexflow.core.subtitles.providers.oss.oss_subtitle import OSSSubtitle
from plexflow.utils.retry.utils import execute_until_success
from plexflow.utils.hooks.redis import UniversalRedisHook
from pathlib import Path
from plexflow.logging.log_setup import logger
import redis
import os

def download_subtitle(subtitle: OSSSubtitle, r: redis.Redis = None, save_dir: Path = Path('.'), skip_exists: bool = True) -> None:
    """
    Downloads and saves the subtitle file using the OpenSubtitlesManager.

    Args:
        subtitle (OSSSubtitle): The subtitle object containing the file ID.

    Returns:
        None
    """
    folder = save_dir / str(subtitle.imdb_code) / subtitle.subtitle.language / str(subtitle.subtitle.id)
    filepath = folder / (str(subtitle.subtitle.file_id) + ".srt")
    metapath = folder / "metadata.json"
    
    if skip_exists and filepath.exists():
        logger.debug(f"Subtitle already exists: {filepath}")
        return str(filepath), True
    else:
        with OpenSubtitlesManager.from_yaml(
            yaml_file=os.getenv("OSS_CREDENTIALS_PATH"),
            r=r,
        ) as manager:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            metapath.write_text(subtitle.subtitle.to_json())
            return manager.download_and_save(subtitle.subtitle.file_id, filename=str(filepath)), False

def download_subtitles(subtitles: List[OSSSubtitle], **kwargs) -> None:
    """
    Downloads subtitles for a list of OSSSubtitle objects.

    Args:
        subtitles (List[OSSSubtitle]): A list of OSSSubtitle objects representing the subtitles to be downloaded.

    Returns:
        None
    """
    r = kwargs.pop("redis", redis.Redis())
    for subtitle in subtitles:
        execute_until_success(download_subtitle, delay_type='constant', delay=3, max_retries=10, subtitle=subtitle, r=r, retry_exceptions=[OpenSubtitlesDownloadQuotaReachedException])