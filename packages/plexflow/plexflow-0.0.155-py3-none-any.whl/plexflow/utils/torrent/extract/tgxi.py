from bs4 import BeautifulSoup
from urllib.parse import urljoin
import dateparser
from plexflow.utils.strings.filesize import parse_size
from plexflow.utils.imdb.imdb_codes import extract_imdb_code


def extract_torrent_results(html):
    """Extracts torrent information from HTML, resilient to HTML structure changes.

    Args:
        html: The HTML content of the page.

    Returns:
        A list of dictionaries, each containing torrent information:
            - 'title': The title of the torrent.
            - 'link': The link to the torrent detail page.
            - 'category': The category of the torrent.
            - 'added': The date the torrent was added.
            - 'size': The size of the torrent.
            - 'seeders': The number of seeders.
            - 'leechers': The number of leechers.
            - 'thumbnail': The URL of the torrent thumbnail (if available).
    """

    torrents = []
    soup = BeautifulSoup(html, 'html.parser')

    # Find all table rows that likely contain torrent information
    rows = soup.find_all('div', class_='tgxtablerow')

    for row in rows:
        torrent = {}

        # Extract data from the cells
        cells = row.find_all('div', class_='tgxtablecell')

        # Title (get full title from link href)
        title_cell = cells[3]
        title_link = title_cell.find('a')
        
        if title_link:
            # Get the part of the href after the last '/'
            torrent['link'] = urljoin('https://torrentgalaxy.info', title_link['href'])
        else:
            torrent['link'] = ''
        
        torrent['name'] = title_cell.text.strip()
        
        # lets search in all links of the cell
        # for an imdb id
        for link in title_cell.find_all('a'):
          href = link.get('href')
          if isinstance(href, str):
            imdb_code = next(extract_imdb_code(href), None)
            if isinstance(imdb_code, str):
              torrent['imdb'] = imdb_code
              break

        # TODO

        torrents.append(torrent)

    return torrents
