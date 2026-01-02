import os
from tvdb_v4_official import TVDB
from typing import Union
from plexflow.core.metadata.providers.tvdb.datatypes import TvdbMovie, movie_from_json, show_from_json
from plexflow.core.metadata.providers.tvdb.tv_datatypes import TvdbShow
import json

def search_movie_by_imdb(imdb_id: str) -> Union[TvdbMovie, None]:
    """
    Search for a movie in TVDB by IMDB ID.

    Args:
        imdb_id (str): The IMDB ID of the movie.

    Returns:
        Union[TvdbMovie, None]: The TvdbMovie object representing the movie if found, None otherwise.
    """
    tvdb = TVDB(os.getenv("TVDB_API_KEY"))
    try:
        response = tvdb.search_by_remote_id(imdb_id)
        if response:
            movie_id = response[0]["movie"]['id']
            movie = tvdb.get_movie_extended(movie_id)
            return movie_from_json(json.dumps(movie))
        else:
            raise ValueError(f"No movie found with IMDB ID {imdb_id}")
    except Exception as e:
        raise e

def search_show_by_imdb(imdb_id: str) -> Union[TvdbShow, None]:
    """
    Searches for a TV show in the TVDB database using the IMDB ID.

    Args:
        imdb_id (str): The IMDB ID of the TV show.

    Returns:
        Union[TvdbShow, None]: An instance of the TvdbShow class representing the TV show if found, 
        otherwise None.

    Raises:
        ValueError: If no TV show is found with the given IMDB ID.
        Exception: If an error occurs during the search.

    """
    tvdb = TVDB(os.getenv("TVDB_API_KEY"))
    try:
        response = tvdb.search_by_remote_id(imdb_id)
        if response:
            show_id = response[0]["series"]['id']
            show = tvdb.get_series_extended(show_id, meta="episodes", short=True)
            return TvdbShow.from_dict(show)
        else:
            raise ValueError(f"No TV show found with IMDB ID {imdb_id}")
    except Exception as e:
        raise e


def get_season(season_id: int) -> dict:
    tvdb = TVDB(os.getenv("TVDB_API_KEY"))
    try:
        response = tvdb.get_season_extended(season_id)
        return response
    except Exception as e:
        raise e
