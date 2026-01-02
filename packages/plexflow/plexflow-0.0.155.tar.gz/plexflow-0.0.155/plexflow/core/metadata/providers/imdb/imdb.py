import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
from plexflow.core.metadata.providers.imdb.datatypes import ImdbMovie, ImdbShow
from typing import Union
import json
import os
import tempfile
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
from urllib.parse import quote

def get_imdb_most_popular_movies(cursor: str = None, persisted_query_hash: str = None, limit: int = 50) -> dict:
    base_url = "https://caching.graphql.imdb.com/"
    
    # 1. Define variables
    variables = {
        "first": limit,
        "locale": "en-US",
        "sortBy": "POPULARITY",
        "sortOrder": "ASC",
        "titleTypeConstraint": {
            "anyTitleTypeIds": ["movie"],
            "excludeTitleTypeIds": []
        }
    }
    if cursor:
        variables["after"] = cursor

    # 2. Define extensions
    extensions = {
        "persistedQuery": {
            "sha256Hash": persisted_query_hash,
            "version": 1
        }
    }

    # 3. Serialize JSON WITHOUT spaces (separators removes spaces after , and :)
    # This is critical. It turns '{"a": 1}' into '{"a":1}' 
    # so that the encoder doesn't see a space and try to add a '+' or '%20'.
    vars_json = json.dumps(variables, separators=(',', ':'))
    ext_json = json.dumps(extensions, separators=(',', ':'))

    # 4. Construct URL manually using quote() instead of quote_plus()
    # quote() uses %20 for spaces (though our minified JSON won't have any).
    # it also encodes {} and "" correctly for a GET request.
    query_string = (
        f"operationName=AdvancedTitleSearch"
        f"&variables={quote(vars_json)}"
        f"&extensions={quote(ext_json)}"
    )

    full_url = f"{base_url}?{query_string}"

    # 5. Headers (Do NOT include 'Content-Type' for a GET request, as it causes the 415 error)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://www.imdb.com",
        "Referer": "https://www.imdb.com/"
    }

    try:
        # Note: We pass full_url directly and don't use the 'params' argument
        response = requests.get(full_url, headers=headers, timeout=15)
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None

def get_imdb_api_credentials_sync(target_url="https://www.imdb.com/search/title/?title_type=movie"):
    """
    Extracts sha256Hash and cursor from IMDb.
    Optimized for Airflow/Docker environments with restricted permissions.
    """
    with sync_playwright() as p:
        # '/tmp' is usually writable in all Airflow/Docker setups.
        user_data_dir = os.path.join(tempfile.gettempdir(), "imdb_playwright_session")
        
        # Ensure the directory exists (tempfile handles this, but let's be safe)
        if not os.path.exists(user_data_dir):
            try:
                os.makedirs(user_data_dir, exist_ok=True)
            except PermissionError:
                # Fallback if /tmp is restricted: use current directory but ensure it's not root
                user_data_dir = os.path.join(os.getcwd(), "imdb_session_local")

        # Launching persistent context
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox", # Essential for running as root/service in Docker
                "--disable-setuid-sandbox"
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        page = context.pages[0] if context.pages else context.new_page()
        api_data = {"hash": None, "cursor": None}

        def intercept_request(request):
            if "AdvancedTitleSearch" in request.url:
                try:
                    parsed = urlparse(request.url)
                    params = parse_qs(parsed.query)
                    if 'extensions' in params:
                        ext = json.loads(params['extensions'][0])
                        api_data["hash"] = ext.get("persistedQuery", {}).get("sha256Hash")
                    if 'variables' in params:
                        var = json.loads(params['variables'][0])
                        if var.get("after"):
                            api_data["cursor"] = var.get("after")
                except:
                    pass

        page.on("request", intercept_request)

        try:
            page.goto(target_url, wait_until="networkidle", timeout=60000)

            # Click Cookie "Accept" if it exists
            page.evaluate("""() => {
                const btn = document.querySelector('button[data-testid="accept-button"]');
                if(btn) btn.click();
            }""")

            # Trigger pagination via JS to avoid hydration issues
            page.evaluate("""() => {
                const btn = document.querySelector('.ipc-see-more__button');
                if (btn) {
                    btn.scrollIntoView();
                    btn.click();
                }
            }""")

            # Poll for results
            for _ in range(20):
                if api_data["hash"] and api_data["cursor"]:
                    break
                page.wait_for_timeout(500)

        finally:
            context.close()

        return api_data

def search_movie_by_imdb(imdb_id: str) -> Union[ImdbMovie, None]:
    """
    Search for a movie using its IMDB ID.

    Args:
        imdb_id (str): The IMDB ID of the movie.

    Returns:
        Union[ImdbMovie, None]: An instance of the ImdbMovie class representing the movie if found, 
        or None if the movie is not found.

    Raises:
        RuntimeError: If an HTTP error, connection error, timeout error, or request exception occurs.
    """
    url = f"https://www.imdb.com/title/{imdb_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }

    try:
        r = requests.get(url=url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as err:
        raise RuntimeError("An error occurred during the request.") from err

    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.select("script[type='application/json']")

    try:
        for script in scripts:
            content = script.text
            data = json.loads(content)
            imdb_id = data.get("props", {}).get("pageProps", {}).get("tconst")
            data = data.get("props", {}).get("pageProps", {}).get("aboveTheFoldData")

            if data:
                title = data.get("originalTitleText", {}).get("text")
                release_day = data.get("releaseDate", {}).get("day")
                release_month = data.get("releaseDate", {}).get("month")
                release_year = data.get("releaseDate", {}).get("year")
                date_str = f"{release_year:04d}-{release_month:02d}-{release_day:02d}"
                release_date = dt.strptime(date_str, "%Y-%m-%d")

                runtime = data.get("runtime", {}).get("seconds")
                rating = data.get("ratingsSummary", {}).get("aggregateRating")
                votes = data.get("ratingsSummary", {}).get("voteCount")
                rank = data.get("meterRanking", {}).get("currentRank")

                return ImdbMovie(imdb_id, title, release_date, runtime, rating, votes, rank)
    except Exception as e:
        print(f"An error occurred: {e}")

    return None


def search_show_by_imdb(imdb_id: str) -> Union[ImdbShow, None]:
    """
    Search for a TV show on IMDb using the IMDb ID.

    Args:
        imdb_id (str): The IMDb ID of the TV show.

    Returns:
        Union[ImdbShow, None]: An instance of the ImdbShow class representing the TV show if found, 
        or None if the TV show is not found.

    Raises:
        RuntimeError: If an HTTP error, connection error, timeout error, or request exception occurs.
    """
    url = f"https://www.imdb.com/title/{imdb_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }

    try:
        r = requests.get(url=url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as err:
        raise RuntimeError("An error occurred during the request.") from err

    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.select("script[type='application/json']")

    try:
        for script in scripts:
            content = script.text
            data = json.loads(content)
            imdb_id = data.get("props", {}).get("pageProps", {}).get("tconst")
            main_data = data.get("props", {}).get("pageProps", {}).get("mainColumnData")
            data = data.get("props", {}).get("pageProps", {}).get("aboveTheFoldData")

            if data:
                title = data.get("originalTitleText", {}).get("text")
                release_day = data.get("releaseDate", {}).get("day")
                release_month = data.get("releaseDate", {}).get("month")
                release_year = data.get("releaseDate", {}).get("year")
                date_str = f"{release_year:04d}-{release_month:02d}-{release_day:02d}"
                release_date = dt.strptime(date_str, "%Y-%m-%d")
                episodes = main_data.get("episodes", {}).get("episodes", {}).get("total")
                seasons = len(set(map(lambda s: s.get("number"), main_data.get("episodes", {}).get("seasons", []))))

                runtime = data.get("runtime", {}).get("seconds")
                rating = data.get("ratingsSummary", {}).get("aggregateRating")
                votes = data.get("ratingsSummary", {}).get("voteCount")
                rank = data.get("meterRanking", {}).get("currentRank")

                return ImdbShow(imdb_id, title, release_date, runtime, rating, votes, rank, episodes, seasons)
    except Exception as e:
        print(f"An error occurred: {e}")

    return None
