from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.imdb.imdb_codes import IMDbCode, extract_imdb_code
import requests
import logging
from plexflow.utils.subtitle.search import SubtitleSearcher
from bs4 import BeautifulSoup

class TorrentReport:
    def __init__(self, **kwargs) -> None:
        self._torrent: Torrent = kwargs.get("torrent")
        self._extracted_imdb_code = kwargs.get("extracted_imdb_code")
        self.hardcoded = kwargs.get("hardcoded")
        self.korsub = kwargs.get("korsub")
        self._subtitles = list(filter(lambda s: s, map(lambda s: s.lower().strip(), kwargs.get("subtitles", []))))
    
    @property
    def torrent(self) -> Torrent:
        return self._torrent
    
    @property
    def extracted_imdb_code(self) -> str:
        return self._extracted_imdb_code
    
    @property
    def imdb_code_matched(self) -> bool:
        return IMDbCode(self.torrent.imdb_code) == IMDbCode(self.extracted_imdb_code)

    @property
    def acceptable_quality(self) -> bool:
        return self.torrent.parsed_release_name.get("quality", "").upper() not in [
            "CAM", "TS", "TC", "SCR", "DVDSCR",
            "SCREENER", "TELESYNC", "TELECINE", "DVDSCREENER",
            "BDSCR", "WEBSCREENER", "HDCAM",
        ]
    @property
    def has_hardcoded_subtitles(self) -> bool:
        return self.torrent.parsed_release_name.get("hardcoded", False) or self.hardcoded
    
    @property
    def has_korsub_subtitles(self) -> bool:
        return self.korsub
    
    @property
    def subtitles(self) -> list:
        return self._subtitles
    
    @property
    def has_native_dutch_subtitles(self):
        return 'dutch' in self.subtitles or 'dut' in self.subtitles
    
    @property
    def has_native_english_subtitles(self):
        return 'english' in self.subtitles or 'eng' in self.subtitles

    @property
    def source(self) -> str:
        return self.torrent.source

class TorrentInspector:
    def __init__(self, torrent: Torrent) -> None:
        self.torrent = torrent
    
    def inspect(self) -> TorrentReport:
        report = {
            "torrent": self.torrent,
        }
        
        logging.info(f"Inspecting torrent: {self.torrent}")
        logging.info(f"Inspecting release name: {self.torrent.release_name}")
        logging.info(f"Inspecting IMDb code: {self.torrent.imdb_code}")
        logging.info(f"Inspecting URL: {self.torrent.url}")
        
        try:
            url = self.torrent.url
            if isinstance(url, str) and len(url) > 0:
                response = requests.get(
                    url=url,
                    headers={
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    }
                )
                response.raise_for_status()

                logging.info(f"URL status code: {response.status_code}")
                
                extracted_imdb_id = next(extract_imdb_code(response.text), None)
                logging.info(f"Extracted IMDb code: {extracted_imdb_id}")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                report["extracted_imdb_code"] = extracted_imdb_id

                # check if torrent has hardcoded subtitles using various alternatives for the word
                # hardcoded
                hardcoded = any([
                    "hardcoded" in self.torrent.release_name.lower(),
                    "hardsub" in self.torrent.release_name.lower(),
                    "hardcoded" in response.text.lower(),
                    "hardsub" in response.text.lower(),
                ])
                
                logging.info(f"Hardcoded subtitles: {hardcoded}")
                
                # check if torrent has korsub subtitles
                korsub = any([
                    "korsub" in self.torrent.release_name.lower(),
                    "korsub" in response.text.lower(),
                ])
                
                logging.info(f"Korsub subtitles: {korsub}")
                
                report["hardcoded"] = hardcoded
                report["korsub"] = korsub
                
                searcher = SubtitleSearcher(hint_words=[
                    "english",
                    "eng",
                    "dutch",
                    "dut",
                ])
                
                subtitles = searcher.search_subtitles(soup.get_text())
                logging.info(f"Subtitles found: {subtitles}")
                report["subtitles"] = subtitles.split(",")
            else:
                logging.info("No URL provided for torrent")
        except Exception as e:
            logging.error(f"Error while inspecting torrent: {e}")

        return TorrentReport(**report)
