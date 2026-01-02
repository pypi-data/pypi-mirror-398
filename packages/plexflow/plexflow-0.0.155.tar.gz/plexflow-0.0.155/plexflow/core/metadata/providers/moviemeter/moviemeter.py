import requests
import os
from typing import Union
from plexflow.core.metadata.providers.moviemeter.datatypes import MovieMeterMovie

def search_movie_by_imdb(imdb_id: str) -> Union[MovieMeterMovie, None]:
    """
    Search for a movie using its IMDB ID.

    Parameters:
    - imdb_id (str): The IMDB ID of the movie.

    Returns:
    - MovieMeterMovie: A MovieMeterMovie object containing all the details of the movie.
    - None: If the movie is not found or an error occurs.

    Example:
    >>> search_movie_by_imdb('tt0111161')
    MovieMeterMovie(title='The Shawshank Redemption', release_date=datetime.datetime(1994, 9, 23, 0, 0), runtime=8520, rating=9.3, votes=2400000, rank=1)
    """
    url = f"https://www.moviemeter.nl/api/film/{imdb_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }
    params = {
        "api_key": os.getenv("MOVIEMETER_API_KEY")
    }

    try:
        r = requests.get(url=url, headers=headers, params=params)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        raise RuntimeError("HTTP Error occurred") from errh
    except requests.exceptions.ConnectionError as errc:
        raise RuntimeError("Connection Error occurred") from errc
    except requests.exceptions.Timeout as errt:
        raise RuntimeError("Timeout Error occurred") from errt
    except requests.exceptions.RequestException as err:
        raise RuntimeError("Request Exception occurred") from err

    data = r.json()
    return MovieMeterMovie.from_dict(data)
