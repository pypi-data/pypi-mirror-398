from typing import List
from pydantic import BaseModel
import subprocess
import re

class SubtitleStream(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    index: int
    language: str

    def __str__(self) -> str:
        return f"SubtitleStream(index={self.index}, language={self.language})"

    def __repr__(self) -> str:
        return self.__str__()

def get_subtitles(video_path: str) -> List[SubtitleStream]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-i", video_path,
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    output = result.stderr.decode("utf-8")

    pattern = re.compile(r'stream\s*#\d+:(\d+)\(([a-z]+)\):\s*subtitle', re.IGNORECASE | re.MULTILINE | re.UNICODE)

    subtitle_streams = []

    matches = re.finditer(pattern, output)

    for match in matches:
        index = int(match.group(1))
        language = match.group(2)
        subtitle_streams.append(SubtitleStream(index=index, language=language))

    return subtitle_streams

def count_subtitles(video_path: str) -> int:
    subtitles = get_subtitles(video_path)
    return len(subtitles)

def has_dutch_subtitles(video_path: str) -> bool:
    subtitles = get_subtitles(video_path)
    return any(subtitle.language.lower() == "nl" for subtitle in subtitles)
