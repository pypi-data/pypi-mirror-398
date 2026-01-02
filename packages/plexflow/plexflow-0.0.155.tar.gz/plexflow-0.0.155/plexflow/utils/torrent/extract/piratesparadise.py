from bs4 import BeautifulSoup
from urllib.parse import urljoin
import dateparser
from plexflow.utils.strings.filesize import parse_size
from plexflow.utils.imdb.imdb_codes import extract_imdb_code


def extract_torrent_results(html):
    torrents = []
    soup = BeautifulSoup(html, 'html.parser')

    # Find all table rows that likely contain torrent information
    rows = soup.select('table tbody tr')

    for row in rows:
        torrent = {}

        rs = row.select('td a.name-link')
        if rs:
            name_link = rs[0]
            torrent['name'] = name_link.text.strip()
            torrent['link'] = 'https://piratesparadise.org' + name_link['href'].strip()
        
        rs = row.select('td:nth-child(2)')
        if rs:
            size_elem = rs[0]
            torrent['size'] = size_elem.text
            torrent['size_bytes'] = next(iter(parse_size(torrent['size'])), None)

        rs = row.select('td .seeds')
        if rs:
            seeds_elem = rs[0]
            try:
                torrent['seeds'] = int(seeds_elem.text)
            except:
                torrent['seeds'] = -1

        rs = row.select('td .peers')
        if rs:
            peers_elem = rs[0]
            try:
                torrent['peers'] = int(peers_elem.text)
            except:
                torrent['peers'] = -1
    
        rs = row.select('td .date-added')
        if rs:
            date_elem = rs[0]
            torrent['added'] = date_elem.text.strip()
            torrent['date'] = dateparser.parse(torrent['added'])

        rs = row.select('td .magnet-btn')
        if rs:
            magnet_elem = rs[0]
            torrent['magnet'] = magnet_elem['onclick'].strip()
            parts = torrent['magnet'].split("('")
            tmp = parts[1]
            parts = tmp.split("')")
            torrent['magnet'] = parts[0].strip()
        torrents.append(torrent)

    return torrents
