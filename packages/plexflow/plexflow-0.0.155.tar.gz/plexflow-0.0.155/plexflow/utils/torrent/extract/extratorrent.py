from bs4 import BeautifulSoup
from plexflow.utils.strings.filesize import parse_size
import dateparser

def extract_torrent_results(html):
    """Extracts torrent results from HTML content, handling dynamic titles, different title structures, and multiple 'a' tags.

    Args:
        html: The HTML content to extract from.

    Returns:
        A list of dictionaries, each representing a torrent result with the following keys:
            - 'title': The title of the torrent.
            - 'size': The size of the torrent.
            - 'seeds': The number of seeders.
            - 'leechers': The number of leechers.
            - 'health': The health of the torrent (as a numerical rating).
            - 'magnet_link': The magnet link for the torrent.
            - 'category': The category of the torrent.
    """

    soup = BeautifulSoup(html, 'html.parser')

    torrents = []
    torrent_rows = soup.find_all('tr', class_=['tlr', 'tlz'])
    for row in torrent_rows:
        torrent = {}

        # Find the correct td (the second one in the row)
        title_td = row.find_all('td', class_='tli')[0] 

        # Find the "view" link (the one with the "view" prefix in the title)
        title_link = title_td.find('a', title=lambda t: t and t.startswith('view ')) 
        if title_link:
            torrent['link'] = 'https://extratorrent.st' + title_link['href']
            torrent['name'] = title_link['title'].replace('view ', '').replace(' torrent', '').strip() 

        torrent['ago'] = row.find_all('td')[2].text.strip()
        if isinstance(torrent['ago'], str):
            torrent['date'] = dateparser.parse(f"{torrent['ago']} ago")

        torrent['size'] = row.find_all('td')[3].text.strip()
        torrent["size_bytes"] = next(iter(parse_size(torrent['size'])), None)
        torrent['seeds'] = row.find_all('td')[4].text.strip()
        torrent['peers'] = row.find_all('td')[5].text.strip()
        torrent['magnet_link'] = row.find('a', title='Magnet link')['href']
        category_span = row.find('span', class_='c_tor')
        if category_span:
            torrent['type'] = category_span.text.strip()
        uploader_span = row.find('span', class_='micro')
        if uploader_span:
            torrent['uploader'] = uploader_span.text.strip()

        torrents.append(torrent)

    return torrents