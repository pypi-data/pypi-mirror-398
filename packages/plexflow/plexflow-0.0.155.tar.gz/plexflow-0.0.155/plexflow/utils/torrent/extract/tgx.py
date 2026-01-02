import re
from bs4 import BeautifulSoup
from plexflow.utils.subtitle.search import SubtitleSearcher
from plexflow.utils.imdb.imdb_codes import extract_imdb_code

def extract_torrent_info(html_content):
    """Extracts torrent information from the provided HTML content,
    searching for IMDb ID pattern in links and plain text.

    Args:
        html_content (str): The HTML content of the webpage.

    Returns:
        dict: A dictionary containing the extracted information with
              lowercase keys, or None if the information is not found.
    """

    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n')

    info = {}

    # release_name
    match = re.search(r"Torrent details for \"(.*?)\"", text)
    info["release_name"] = match.group(1).lower() if match else None

    # category and subcategory
    match = re.search(
        r"Category:\s*(.*?)\s*>\s*(.*?)$", text, re.MULTILINE
    )
    info["category"] = match.group(1).strip().lower() if match else None
    info["subcategory"] = match.group(2).strip().lower() if match else None

    # language
    match = re.search(r"Language:\s*(.*?)$", text, re.MULTILINE)
    info["language"] = match.group(1).strip().lower() if match else None

    # total_size (Handling different units)
    match = re.search(r"Total Size:\s*([\d.]+)\s*(GB|MB|KB)", text, re.IGNORECASE)
    if match:
        size_value = float(match.group(1))
        size_unit = match.group(2).upper()
        if size_unit == "GB":
            info["total_size"] = size_value * 1024 * 1024 * 1024
        elif size_unit == "MB":
            info["total_size"] = size_value * 1024 * 1024
        elif size_unit == "KB":
            info["total_size"] = size_value * 1024
    else:
        info["total_size"] = None

    # hash
    match = re.search(r"Info Hash:\s*(.*?)$", text, re.MULTILINE)
    info["hash"] = match.group(1).strip().lower() if match else None

    # uploader
    match = re.search(r"Added By:\s*(.*?)\s*Added", text, re.MULTILINE)
    info["uploader"] = match.group(1).strip().lower() if match else None

    # date
    match = re.search(r"Added:\s*(.*?)$", text, re.MULTILINE)
    info["date"] = match.group(1).strip().lower() if match else None

    # seeds
    match = re.search(r"Seeds:?\s*(\d+)", text)
    info["seeds"] = int(match.group(1)) if match else None

    # peers
    match = re.search(r"Leechers:?\s*(\d+)", text)
    info["peers"] = int(match.group(1)) if match else None

    # imdb_id
    imdb_id = next(extract_imdb_code(html_content), None)
    info["imdb_id"] = imdb_id

    # description (Extract up to the comments section)
    match = re.search(
        r"Description(.*?)User comments", text, re.IGNORECASE | re.DOTALL
    )
    info["description"] = match.group(1).strip().lower() if match else None

    # magnet_url
    match = re.search(r"magnet:\?xt=urn:btih:[a-z0-9]+[^'\"]+", html_content, re.IGNORECASE)
    info["magnet_url"] = match.group(0) if match else None 
    
    searcher = SubtitleSearcher(hint_words={
        "english",
        "eng",
        "dutch",
        "dut"
    })
    
    subtitles = searcher.search_subtitles(text)
    info["subtitles"] = subtitles
    
    return info