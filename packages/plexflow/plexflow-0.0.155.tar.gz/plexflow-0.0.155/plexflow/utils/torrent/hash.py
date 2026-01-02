import re
from bs4 import BeautifulSoup

def extract_hash(s: str):
    """
    Extract all potential SHA-1 hashes from an arbitrary string.

    This function uses a generator to lazily yield each potential hash as it is found,
    which can be more memory-efficient than returning a list of all hashes, especially
    for large input strings with many potential hashes.

    Parameters:
    s (str): The string from which to extract the potential hashes.

    Yields:
    str: Each extracted potential hash.

    Examples:
    >>> list(extract_hash('Here is a SHA-1 hash: 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'))
    ['5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8']

    >>> list(extract_hash('No hashes here!'))
    []
    """
    # Regular expression pattern for a SHA-1 hash
    pattern = r'\b[A-Fa-f0-9]{40}\b'

    # Find all matches of the pattern in the input string
    for match in re.finditer(pattern, s):
        # Yield each match
        yield match.group(0)


def extract_torrent_hash(magnet: str):
    """
    Extract the torrent hash from a magnet link.

    This function calls the `extract_hash` function to find potential SHA-1 hashes in the magnet link.
    The torrent hash is typically found after 'xt=urn:btih:' in the magnet link.

    Parameters:
    magnet (str): The magnet link from which to extract the torrent hash.

    Returns:
    str: The extracted torrent hash, or None if no hash was found.

    Examples:
    >>> extract_torrent_hash('magnet:?xt=urn:btih:5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8')
    '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'

    >>> extract_torrent_hash('No hashes here!')
    None
    """
    # Find the start of the torrent hash in the magnet link
    start = magnet.find('xt=urn:btih:') + len('xt=urn:btih:')

    # Extract the potential hashes from the substring starting at the start index
    hashes = extract_hash(magnet[start:])

    # Return the first hash found, or None if no hash was found
    return next(hashes, None)


def extract_magnet(text: str):
    """
    Extract magnet links from an arbitrary string.

    This function uses a generator to lazily yield each magnet link as it is found,
    which can be more memory-efficient than returning a list of all links, especially
    for large input strings with many potential links.

    Parameters:
    text (str): The string from which to extract the magnet links.

    Yields:
    str: Each extracted magnet link.

    Examples:
    >>> list(extract_magnet('Here is a magnet link: magnet:?xt=urn:btih:5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'))
    ['magnet:?xt=urn:btih:5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8']

    >>> list(extract_magnet('No magnet links here!'))
    []
    """
    # Regular expression pattern for a magnet link
    pattern = r'magnet:\?xt=urn:btih:[A-Fa-f0-9]+'

    # Find all matches of the pattern in the input string
    for match in re.finditer(pattern, text, re.IGNORECASE):
        # Yield each match
        yield match.group(0)


def extract_magnet_from_html(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('a', href=re.compile(r'magnet:\?xt=urn:btih:[A-Fa-f0-9]+'))