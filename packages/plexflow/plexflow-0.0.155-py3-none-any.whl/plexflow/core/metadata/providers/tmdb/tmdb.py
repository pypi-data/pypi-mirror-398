import os
import tmdbsimple
from tmdbsimple import Find, Movies, TV, TV_Seasons
from typing import Union, List
from plexflow.core.metadata.providers.tmdb.datatypes import TmdbMovie, TmdbShow, movie_from_json, show_from_json, TmdbSeason
import json

def search_movie_by_imdb(imdb_id: str) -> Union[TmdbMovie, None]:
    """
    Search for a movie using its IMDB ID.

    Parameters:
    imdb_id (str): The IMDB ID of the movie.

    Returns:
    Movie: A Movie object containing all the details of the movie.
    None: If the movie is not found or an error occurs.

    Example:
    >>> search_movie_by_imdb('tt0111161')
    Movie(id=278, title='The Shawshank Redemption', overview='Framed in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at the Shawshank prison, where he puts his accounting skills to work for an amoral warden. During his long stretch in prison, Dufresne comes to be admired by the other inmates -- including an older prisoner named Red -- for his integrity and unquenchable sense of hope.', release_date='1994-09-23', ...)
    """
    tmdbsimple.API_KEY = os.getenv("TMDB_API_KEY")

    try:
        find = Find(imdb_id)
        response = find.info(external_source='imdb_id')
        if response['movie_results']:
            movie_id = response['movie_results'][0]['id']
            movie = Movies(movie_id)
            info = movie.info(append_to_response="alternative_titles")
            return movie_from_json(json.dumps(info))
        else:
            raise ValueError(f"No movie found with IMDB ID {imdb_id}")
    except Exception as e:
        raise e

def search_show_by_imdb(imdb_id: str) -> Union[TmdbShow, None]:
    """
    Search for a TV show using its IMDB ID.

    Parameters:
    imdb_id (str): The IMDB ID of the TV show.

    Returns:
    Show: A Show object containing all the details of the TV show.
    None: If the TV show is not found or an error occurs.

    Example:
    >>> search_show_by_imdb('tt0944947')
    Show(id=1399, name='Game of Thrones', overview='Seven noble families fight for control of the mythical land of Westeros. Friction between the houses leads to full-scale war. All while a very ancient evil awakens in the farthest north. Amidst the war, a neglected military order of misfits, the Night\'s Watch, is all that stands between the realms of men and icy horrors beyond.', first_air_date='2011-04-17', ...)
    """
    tmdbsimple.API_KEY = os.getenv("TMDB_API_KEY")

    try:
        find = Find(imdb_id)
        response = find.info(external_source='imdb_id')
        if response['tv_results']:
            show_id = response['tv_results'][0]['id']
            show = TV(show_id)
            info = show.info(append_to_response="alternative_titles,external_ids")
            return show_from_json(json.dumps(info))
        else:
            raise ValueError(f"No TV show found with IMDB ID {imdb_id}")
    except Exception as e:
        raise e


def get_season_by_show_id(tmdb_id: int, season: int) -> TmdbSeason:
    tmdbsimple.API_KEY = os.getenv("TMDB_API_KEY")

    try:
        tv = TV_Seasons(tv_id=tmdb_id, season_number=season)
        response = tv.info()
        return TmdbSeason.from_dict(response)
    except Exception as e:
        raise e

def get_all_seasons_by_imdb_id(imdb_id: str) -> List[TmdbSeason]:
    show = search_show_by_imdb(imdb_id=imdb_id)
    results = []
    for season in show.seasons:
        season_info = get_season_by_show_id(tmdb_id=show.id, season=season.season_number)
        results.append(season_info)
    return results
