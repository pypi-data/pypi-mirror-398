import urllib.parse

def build_url(base_url: str, path: str, query_params: dict) -> str:
    # Construct the full URL
    url = urllib.parse.urljoin(base_url, path)
    # Add query parameters
    query_string = urllib.parse.urlencode(query_params if query_params else {})
    full_url = f"{url}?{query_string}"
    return full_url
