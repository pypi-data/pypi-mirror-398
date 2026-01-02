from plexflow.core.subtitles.providers.oss.search import get_subtitles, OSSSubtitle
from typing import List, Iterator, Any
from plexflow.utils.hooks.redis import UniversalRedisHook
from plexflow.core.subtitles.providers.oss.download import download_subtitle    
from tqdm import tqdm
from plexflow.core.subtitles.providers.oss.unlimited_oss import OpenSubtitlesDownloadQuotaReachedException
from plexflow.utils.retry.utils import execute_until_success
import time
from pathlib import Path
from plexflow.logging.log_setup import logger
import redis

class AutoSubtitles:
    """
    A class that represents an auto subtitles provider.

    Attributes:
        imdb_id (str): The IMDb ID of the movie or TV show.
        languages (List[str]): A list of languages for which subtitles are requested.
        kwargs: Additional keyword arguments.

    """
    def __init__(self, imdb_id: str, languages: List[str] = (), **kwargs: Any) -> None:
        self.imdb_id = imdb_id
        self.languages = languages
        self.redis = kwargs.pop("redis", redis.Redis())
        self.download = kwargs.pop("download", False)
        self.download_folder = Path(kwargs.pop("download_folder", Path(".")))
        self.kwargs = kwargs
    
    def __iter__(self) -> Iterator[OSSSubtitle]:
        subtitles = get_subtitles(self.imdb_id, self.languages, self.redis, ignore_blacklist=True, **self.kwargs)
        if len(subtitles) == 0:
            logger.warning(f"No subtitles found for IMDb ID: {self.imdb_id}")
            return
        
        for subtitle in tqdm(subtitles, total=len(subtitles)):
            if self.download:
                subtitle_path, skipped = execute_until_success(download_subtitle, delay_type='constant', delay=3, max_retries=10, subtitle=subtitle, r=self.redis, retry_exceptions=[OpenSubtitlesDownloadQuotaReachedException], save_dir=self.download_folder)
                if not skipped:
                    logger.debug(f"Subtitle downloaded: {subtitle_path}")
                    # time.sleep(1.2)
            yield subtitle, subtitle_path        
    
    def __next__(self) -> Any:
        try:
            return next(self.__iter__())
        except StopIteration:
            raise
