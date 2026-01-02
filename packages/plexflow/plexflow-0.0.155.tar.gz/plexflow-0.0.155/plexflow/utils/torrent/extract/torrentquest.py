from bs4 import BeautifulSoup
import dateparser
from plexflow.utils.strings.filesize import parse_size
import re
from plexflow.utils.strings.filesize import parse_size
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

    # Torrent name
    # Extract the text from the 'header-content' class
    torrent_details['release_name'] = soup.find('div', class_='header-content').get_text().strip()

    # Extract all text from the HTML
    all_text = soup.get_text()

    # Torrent size (capture only the number)
    size_text = re.search(r'Total Size:\s*(\d+\.?\d*\s*\w+)', all_text, re.IGNORECASE)
    if size_text:
        torrent_details['torrent_size'] = size_text.group(1).strip()
        torrent_details["size_bytes"] = next(iter(parse_size(torrent_details['torrent_size'])), None)

    # Peers (Leechers)
    peers_text = re.search(r'Leechers:\s*\d+', all_text, re.IGNORECASE)
    if peers_text:
        torrent_details['peers'] = int(peers_text.group(0).split()[-1])

    # Seeds
    seeds_text = re.search(r'Seeders:\s*\d+', all_text, re.IGNORECASE)
    if seeds_text:
        torrent_details['seeds'] = int(seeds_text.group(0).split()[-1])

    # Total files
    files_text = re.search(r'Total Files:\s*\d+', all_text, re.IGNORECASE)
    if files_text:
        torrent_details['total_files'] = int(files_text.group(0).split()[-1])

    # Date of upload
    upload_text = re.search(r'Uploaded:\s*\d{1,2}-\w{3}-\d{4}', all_text, re.IGNORECASE)
    if upload_text:
        torrent_details['date'] = upload_text.group(0).split()[-1]

    # Uploader
    uploader_text = re.search(r'Uploader:\s*\w+', all_text, re.IGNORECASE)
    if uploader_text:
        torrent_details['uploader'] = uploader_text.group(0).split()[-1]

    # Info hash
    info_hash_text = re.search(r'Info Hash:\s*[\dA-F]+', all_text, re.IGNORECASE)
    if info_hash_text:
        torrent_details['hash'] = info_hash_text.group(0).split()[-1]

    # File list (extract from text using surrounding context)
    torrent_details['file_list'] = []
    file_list_start = re.search(r'File List Information', all_text, re.IGNORECASE)
    if file_list_start:
        file_list_start_index = file_list_start.end()
        file_list_end = re.search(r'Related Downloads|Help Downloading', all_text, re.IGNORECASE)
        if file_list_end:
            file_list_end_index = file_list_end.start()
            file_list_text = all_text[file_list_start_index:file_list_end_index]
            
            file_entries = file_list_text.strip().splitlines()
            
            for entry in file_entries:
                # Extract file name and size
                name_match = re.search(r'(.+)\s*\(\d+\.?\d*\s*(GB|MB|KB|B)\)', entry, re.IGNORECASE)
                # the size is always at the end, so lets search from the end
                size_matches = re.findall(r'\(([^)]+)\)', entry, re.IGNORECASE)
                print(size_matches)
                
                name = name_match.group(1).strip() if name_match else None
                if len(size_matches) > 0:
                    size = size_matches[-1].strip()
                else:
                    size = None
                                
                torrent_details['file_list'].append(TorrentFile(
                    name=name,
                    size=size,
                ))

    # Category
    category_text = re.search(r'Category:\s*\w+', all_text, re.IGNORECASE)
    if category_text:
        torrent_details['category'] = category_text.group(0).split()[-1]

    return torrent_details


def extract_torrent_results(html):
    """
    Extracts torrent results from HTML content, resilient to changes in HTML structure.

    Args:
        html: The HTML content as a string.

    Returns:
        A list of dictionaries, each representing a torrent result with keys:
            - 'download_name': The name of the torrent.
            - 'magnet_link': The magnet link for the torrent.
            - 'age': The age of the torrent.
            - 'torrent_type': The type of the torrent (e.g., Movie, Game, etc.).
            - 'files': The number of files in the torrent.
            - 'size': The size of the torrent.
            - 'seeders': The number of seeders for the torrent.
            - 'leechers': The number of leechers for the torrent.
    """

    soup = BeautifulSoup(html, 'html.parser')
    torrent_results = []

    # Find all 'a' tags with 'magnet' in the href attribute
    magnet_links = soup.find_all('a', href=lambda href: 'magnet' in href)

    # Iterate over each magnet link
    for magnet_link in magnet_links:
        torrent_result = {'magnet_link': magnet_link['href']}

        # Find the parent 'tr' (table row) of the magnet link
        parent_row = magnet_link.find_parent('tr')
        if parent_row:
            cols = parent_row.find_all('td')

            # Extract data from columns based on their position 
            # (assuming consistent layout within the table row)
            if len(cols) >= 8:
                torrent_result['name'] = cols[1].find('a').text.strip()
                # get link of name
                link = cols[1].find('a')['href']
                # make it a full link
                torrent_result['link'] = f"https://torrentquest.com{link}"
                age = cols[2].text.strip()
                torrent_result['age'] = age
                if isinstance(age, str):
                    age_str = f"{age} ago"
                    date = dateparser.parse(age_str)
                    torrent_result['date'] = date
                else:
                    torrent_result['date'] = None
                torrent_result['type'] = cols[3].text.strip().lower()
                torrent_result['files'] = cols[4].text.strip()
                size_human = cols[5].text.strip()
                torrent_result['size'] = size_human

                if isinstance(size_human, str):
                    sizes = parse_size(size_human)
                    if sizes:
                        torrent_result['size_bytes'] = sizes[0]
                    else:
                        torrent_result['size_bytes'] = None
                
                torrent_result['seeds'] = cols[6].text.strip()
                torrent_result['peers'] = cols[7].text.strip()

        torrent_results.append(torrent_result)

    return torrent_results
