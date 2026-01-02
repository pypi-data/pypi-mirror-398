from bs4 import BeautifulSoup
from urllib.parse import urljoin
import dateparser
from plexflow.utils.strings.filesize import parse_size
from plexflow.utils.imdb.imdb_codes import extract_imdb_code
import re
from plexflow.utils.torrent.files import TorrentFile
from plexflow.utils.torrent.extract.common import torrent_detail_extract

@torrent_detail_extract
def extract_torrent_details(html_content, **torrent_details):
    """Extracts specific torrent details from the given HTML content,
       with increased robustness against HTML structure changes and case sensitivity.

    Args:
        html_content: The HTML content of the torrent page.

    Returns:
        A dictionary containing the extracted torrent details.
    """

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract all text from the HTML
    all_text = soup.get_text()

    # Torrent name
    torrent_details['release_name'] = re.search(r':\s*([^:]+)\s*:\s*Search', all_text, re.IGNORECASE).group(1).strip()

    # Torrent size (capture only the number)
    size_text = re.search(r'Size:\s*(\d+\.?\d*\s*\w+)', all_text, re.IGNORECASE)
    if size_text:
        torrent_details['torrent_size'] = size_text.group(1).strip()
        torrent_details["size_bytes"] = next(iter(parse_size(torrent_details['torrent_size'])), None)

    # Peers (Leechers)
    peers_text = re.search(r'Leechers:\s*(\d+)', all_text, re.IGNORECASE)
    if peers_text:
        torrent_details['peers'] = int(peers_text.group(1))

    # Seeds
    seeds_text = re.search(r'Seeders:\s*(\d+)', all_text, re.IGNORECASE)
    if seeds_text:
        torrent_details['seeds'] = int(seeds_text.group(1))

    # Total files
    files_text = re.search(r'Files:\s*(\d+)', all_text, re.IGNORECASE)
    if files_text:
        torrent_details['total_files'] = int(files_text.group(1))

    # Date of upload
    upload_text = re.search(r'Added:\s*([^,]+)', all_text, re.IGNORECASE)
    if upload_text:
        torrent_details['date'] = dateparser.parse(upload_text.group(1).strip()).isoformat()

    # Uploader
    uploader_text = re.search(r'Uploader:\s*([^<]+)', all_text, re.IGNORECASE)
    if uploader_text:
        torrent_details['uploader'] = uploader_text.group(1).strip()

    # Info hash
    info_hash_text = re.search(r'Info Hash:\s*([\dA-F]+)', all_text, re.IGNORECASE)
    if info_hash_text:
        torrent_details['hash'] = info_hash_text.group(1).strip()

    # File list (extract from text using surrounding context)
    torrent_details['file_list'] = []
    file_list_start = re.search(r'Files:\s*\d+', all_text, re.IGNORECASE)
    if file_list_start:
        file_list_start_index = file_list_start.end()
        file_list_end = re.search(r'Multiple Quality Available', all_text, re.IGNORECASE)
        if file_list_end:
            file_list_end_index = file_list_end.start()
            file_list_text = all_text[file_list_start_index:file_list_end_index]
            
            file_entries = file_list_text.strip().splitlines()
            
            for entry in file_entries:
                # Extract file name and size
                name_match = re.search(r'(.+)\s*(\d+\.?\d*\s*(GB|MB|KB|B))', entry, re.IGNORECASE)
                name = name_match.group(1).strip() if name_match else None
                size = name_match.group(2).strip() if name_match else None
                                
                torrent_details['file_list'].append(TorrentFile(
                    name=name,
                    size=size,
                ))

    # Category
    category_text = re.search(r'Category:\s*([^<]+)', all_text, re.IGNORECASE)
    if category_text:
        torrent_details['category'] = category_text.group(1).strip()

    return torrent_details


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
    rows = soup.find_all('tr', class_='list-entry')

    for row in rows:
        torrent = {}

        # Extract data from the cells
        cells = row.find_all('td')

        # Title (get full title from link href)
        title_cell = cells[1]
        title_link = title_cell.find('div', class_='wrapper').find('a', recursive=False)
        if title_link:
            # Get the part of the href after the last '/'
            torrent['link'] = urljoin('https://therarbg.com/', title_link['href'])
            torrent['name'] = torrent['link'].rstrip('/').split('/')[-1]  # Use rsplit for last occurrence
        else:
            # If no link is found, get the text of the title cell
            torrent['name'] = title_cell.text.strip()
            torrent['link'] = ''

        # lets search in all links of the cell
        # for an imdb id
        for link in title_cell.find_all('a'):
          href = link.get('href')
          if isinstance(href, str):
            imdb_code = next(extract_imdb_code(href), None)
            if isinstance(imdb_code, str):
              torrent['imdb'] = imdb_code
              break
            
        # Category
        torrent['type'] = cells[2].find('a').text.strip() if cells[2].find('a') else ''

        # Added
        added_cell = cells[3]
        torrent['added'] = added_cell.text.strip() if added_cell else ''
        torrent['date'] = dateparser.parse(torrent['added'])
        
        # Size
        size_cell = cells[5]
        torrent['size'] = size_cell.text.strip() if size_cell else ''
        torrent['size_bytes'] = next(iter(parse_size(torrent['size'])), None)
        
        # Seeders and Leechers
        seeders_cell = cells[6]
        torrent['seeds'] = int(seeders_cell.text.strip()) if seeders_cell else 0
        leechers_cell = cells[7]
        torrent['peers'] = int(leechers_cell.text.strip()) if leechers_cell else 0

        torrents.append(torrent)

    return torrents
