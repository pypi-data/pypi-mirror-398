from plexflow.core.subtitles.providers.oss.search import get_subtitles
from plexflow.core.subtitles.providers.oss.download import download_subtitles
from plexflow.core.subtitles.providers.auto_subtitles import AutoSubtitles
from pathlib import Path
from typing import List

auto_subtitles = AutoSubtitles(
    imdb_id="tt8367814",
    languages=["nl", "en"],
    credentials_path="config/credentials.yaml",
    redis_host="localhost",
    redis_port=6379,
)

download_subtitles(auto_subtitles)
