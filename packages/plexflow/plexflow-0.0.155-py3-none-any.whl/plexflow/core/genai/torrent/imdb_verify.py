from plexflow.core.genai.bot import CohereBot
import json
import requests
from bs4 import BeautifulSoup

class TorrentImdbMatcher(CohereBot):
    def __init__(self) -> None:
        super().__init__(preamble_id="torrent_imdb_matcher")
    
    def parse(self, content: str):
        response = self.co.chat(
            message=content,
            temperature=1,
            model="command-r-plus",
            preamble=self.preamble,
        )
        
#        print(response.json())
        content = response.text
        
        if content.startswith('```json'):
            content = content.lstrip("`json")
        
        if content.endswith('`'):
            content = content.rstrip("`")

        return json.loads(content)

def get_page_text(url):
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Cookie": r"dom3ic8zudi28v8lr6fgphwffqoz0j6c=b7c768c9-98eb-49e8-8ec5-2c9e5c5828c9%3A2%3A1; sb_main_755b5f8e271690d6cb76076f459e9c82=1; PHPSESSID=g2g6grs8ejkoqisi81h1tomtk6; sb_count_755b5f8e271690d6cb76076f459e9c82=4; hu8935j4i9fq3hpuj9q39=true; fencekey=8ad2dbbf2b3ba78729048b3d823574ee; AdskeeperStorage=%7B%220%22%3A%7B%22svspr%22%3A%22%22%2C%22svsds%22%3A9%7D%2C%22C1543068%22%3A%7B%22page%22%3A5%2C%22time%22%3A%221718527871490%22%7D%2C%22C1343686%22%3A%7B%22page%22%3A5%2C%22time%22%3A%221718527871482%22%7D%2C%22C385455%22%3A%7B%22page%22%3A5%2C%22time%22%3A%221718527871553%22%7D%7D"
        }
    )
    
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    return soup.get_text()

def matches_with_imdb(imdb_id: str, torrent_url: str):
    parser = TorrentImdbMatcher()

    imdb_info = get_page_text(f"https://www.imdb.com/title/{imdb_id}")
    torrent_info = get_page_text(torrent_url)
    
    prompt = f"""
    IMDB INFO:
    {imdb_info}
    
    TORRENT INFO:
    {torrent_info}
    """

    print("prompt has", len(prompt), "chars")

    data = parser.parse(prompt)
    
    matched = data.get("match")
    reasons = data.get("reasons", [])
    
    return matched, reasons
