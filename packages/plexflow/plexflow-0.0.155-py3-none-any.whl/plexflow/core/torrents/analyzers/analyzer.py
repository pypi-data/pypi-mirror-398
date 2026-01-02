from plexflow.core.torrents.results.torrent import Torrent
import requests
from plexflow.core.torrents.analyzers.analyzed_torrent import AnalyzedTorrent
from abc import ABC, abstractmethod

class TorrentAnalyzer(ABC):
    def __init__(self, torrent: Torrent):
        self._torrent = torrent

        self._resolved_urls = self.resolve_urls()
        self._full_urls_content = '\n\n'.join(self._resolved_urls.values())        

    def resolve_urls(self):
        resolved_urls = {}
        
        if self._torrent.url:
            print(f"Resolving URL: {self._torrent.url}")
            r = requests.get(
                url=self._torrent.url,
                headers=self._headers,
            )
            
            r.raise_for_status()
            
            html = r.text
            
            resolved_urls[self._torrent.url] = html
        else:
            print(f"Torrent {self._torrent} does not have a URL.")

        return resolved_urls

    @abstractmethod
    def do_analysis(self):
        pass
    
    def analyze(self):
        details = self.do_analysis()
        if isinstance(details, dict):
            details = {
                **details,
                'resolved_urls': self._resolved_urls,
                'html_content': self._full_urls_content,
            }
        return AnalyzedTorrent(self._torrent, **details)