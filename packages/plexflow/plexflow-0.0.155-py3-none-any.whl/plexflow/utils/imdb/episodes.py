import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from plexflow.utils.imdb.imdb_codes import extract_imdb_code

def get_imdb_episode_codes(imdb_title_id: str, season_number: int) -> Dict[int, Optional[str]]:
    """
    Fetches IMDb episode codes for a given title ID and season number.

    Args:
        imdb_title_id (str): The IMDb title ID (e.g., 'tt3581920').
        season_number (int): The season number to retrieve episodes for.

    Returns:
        Dict[int, Optional[str]]: A dictionary where keys are episode numbers
                                  and values are their corresponding IMDb codes.
                                  Returns an empty dictionary if no episodes are found or
                                  an error occurs.
    """
    if not imdb_title_id.startswith('tt'):
        print("Warning: IMDb title ID should start with 'tt'.")
        return {}

    url = f"https://www.imdb.com/title/{imdb_title_id}/episodes/?season={season_number}&ref_=ttep"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15',
    }

    try:
        r = requests.get(url=url, headers=headers, timeout=10) # Added timeout for robustness
        r.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return {}

    soup = BeautifulSoup(r.text, 'html.parser')

    # Select all <a> tags within elements that have class 'episode-item-wrapper'
    # and whose href attribute starts with '/title/'.
    links = soup.select('.episode-item-wrapper a[href^="/title/"]')

    episodes: Dict[int, Optional[str]] = {}
    seen_urls = set()
    current_episode_number = 1

    for link in links:
        href = link['href']
        # IMDb often lists the same episode link multiple times (e.g., image and title link).
        # We only want to process each unique episode URL once.
        if href not in seen_urls:
            seen_urls.add(href)
            # The extract_imdb_code function should return the IMDb code directly,
            # not an iterator, based on common usage. If it returns an iterator,
            # `next(..., None)` is correct.
            episode_imdb_code = next(extract_imdb_code(href), None)
            if episode_imdb_code: # Only add if a valid IMDb code was extracted
                episodes[current_episode_number] = episode_imdb_code
                current_episode_number += 1

    return episodes
