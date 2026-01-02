from plexflow.core.torrents.results.torrent import Torrent
from plexflow.utils.torrent.extract.torrentquest import extract_torrent_details
import requests
import re
from plexflow.core.torrents.analyzers.analyzed_torrent import AnalyzedTorrent
from plexflow.core.torrents.analyzers.analyzer import TorrentAnalyzer

class TorrentQuestAnalyzer(TorrentAnalyzer):
    def __init__(self, torrent: Torrent):
        self._nfo_link_pattern = re.compile(r"information\('file_([^']+)'\)", re.IGNORECASE)

        self._headers= {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        }
        
        super().__init__(torrent)

    def resolve_urls(self):
        resolved_urls = super().resolve_urls()
        
        if len(resolved_urls) > 0:
            html = next(iter(resolved_urls.values()))
            nfo_match = next(re.finditer(self._nfo_link_pattern, html), None)
            
            if nfo_match:
                nfo_id = nfo_match.group(1)
                nfo_url = f"https://torrentquest.com/info/{nfo_id}"
                
                print(f"Resolving NFO URL: {nfo_url}")
                r_nfo = requests.get(
                    url=nfo_url,
                    headers=self._headers,
                )
                
                r_nfo.raise_for_status()
                
                nfo_html = r_nfo.text
                
                resolved_urls[nfo_url] = nfo_html
        
        return resolved_urls
    
    def do_analysis(self):
        # resolve torrent URL and extract the torrent information from the page
        details = extract_torrent_details(self._full_urls_content)
        return details
