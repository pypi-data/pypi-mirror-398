from plexflow.utils.subtitle.search import SubtitleSearcher
from bs4 import BeautifulSoup
from plexflow.utils.imdb.imdb_codes import extract_imdb_code
from plexflow.utils.torrent.hash import extract_magnet
from plexflow.utils.torrent.files import TorrentSubtitle
from plexflow.utils.strings.language import get_language_code

def torrent_detail_extract(func):
    def wrapper(html):
        searcher = SubtitleSearcher(
            hint_words={
                "dutch",
                "dut",
                "eng",
                "english",
            }
        )

        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        subtitles = searcher.search_subtitles(text)
        
        imdb_code = next(extract_imdb_code(html), None)

        magnet = next(extract_magnet(text), None)

        details = {
            "subtitles": [TorrentSubtitle(name=sub, language=get_language_code(sub)) for sub in filter(lambda s: s.strip(), subtitles.split(","))],
            "imdb_id": imdb_code,
            "magnet": magnet,
        }

        # Call the decorated function with the HTML and extracted parts as a dictionary
        return func(html, **details)

    return wrapper

