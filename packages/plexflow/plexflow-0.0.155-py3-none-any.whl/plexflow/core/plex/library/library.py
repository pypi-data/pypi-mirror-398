from plexflow.core.plex.api.context.library import PlexLibraryRequestContext
import os

def get_library_id(library_name: str) -> int:
    """
    Get the ID of a Plex library based on its name.

    Parameters:
    library_name (str): The name of the Plex library.

    Returns:
    int: The ID of the Plex library.

    Raises:
    ValueError: If the library name is not found.

    Examples:
    >>> get_library_id('Movies')
    1
    >>> get_library_id('TV Shows')
    2
    """
    context = PlexLibraryRequestContext()
    response = context.get(f"/library/sections")
    
    data = response.json()
    sections = data["MediaContainer"]["Directory"]
    for section in sections:
        if section["title"] == library_name:
            return section["key"]
    raise ValueError(f"Library '{library_name}' not found.")

def refresh_library(library_name: str) -> bool:
    library_id = get_library_id(library_name)
    context = PlexLibraryRequestContext()
    context.get(f"/library/sections/{library_id}/refresh")

def refresh_movies_library(library_name: str = "Films") -> bool:
    return refresh_library(library_name=library_name)

def refresh_tv_library(library_name: str = "Series") -> bool:
    return refresh_library(library_name=library_name)

def is_media_in_library(guid: str, library_name: str, media_type: str) -> bool:
    """
    Check if a media exists in a Plex library based on its GUID.

    Parameters:
    guid (str): The GUID of the media to search for.
    library_name (str): The name of the Plex library.
    media_type (str): The type of media (e.g., 'movie', 'show').

    Returns:
    bool: True if the media is found in the library, False otherwise.

    Examples:
    >>> is_media_in_library('plex://movie/65581f1fb67b7b5555369f9c', 'Movies', 'movie')
    True
    >>> is_media_in_library('plex://show/65581f1fb67b7b5555369f9c', 'TV Shows', 'show')
    False
    """
    library_id = get_library_id(library_name)
    context = PlexLibraryRequestContext()
    response = context.get(f"/library/sections/{library_id}/all", params={
        "guid": guid
    })
    
    data = response.json()
    n_results = data["MediaContainer"]["size"]

    if media_type == 'movie':
        return n_results > 0
    elif media_type == 'show':
        return n_results > 0
    else:
        raise ValueError(f"Invalid media type: {media_type}")
    
def is_movie_in_library(guid: str, library_name: str = 'Films') -> bool:
    """
    Check if a movie exists in a Plex library based on its GUID.

    Parameters:
    guid (str): The GUID of the movie to search for.
    library_name (str): The name of the Plex library. Default is 'Films'.

    Returns:
    bool: True if the movie is found in the library, False otherwise.

    Examples:
    >>> is_movie_in_library('plex://movie/65581f1fb67b7b5555369f9c', 'Movies')
    True
    >>> is_movie_in_library('plex://show/65581f1fb67b7b5555369f9c', 'TV Shows')
    False
    """
    return is_media_in_library(guid, library_name, 'movie')

def is_show_in_library(guid: str, library_name: str = 'Series') -> bool:
    """
    Check if a TV show exists in a Plex library based on its GUID.

    Parameters:
    guid (str): The GUID of the TV show to search for.
    library_name (str): The name of the Plex library. Default is 'Series'.

    Returns:
    bool: True if the TV show is found in the library, False otherwise.

    Examples:
    >>> is_show_in_library('plex://movie/65581f1fb67b7b5555369f9c', 'Movies')
    True
    >>> is_show_in_library('plex://show/65581f1fb67b7b5555369f9c', 'TV Shows')
    False
    True
    """
    return is_media_in_library(guid, library_name, 'show')

def get_library_imdb_ids(library_name: str) -> set:
    from plexapi.server import PlexServer

    baseurl = f'http://{os.getenv("PLEX_HOST")}:{os.getenv("PLEX_PORT", 32400)}'
    token = os.getenv("PLEX_TOKEN")
    plex = PlexServer(baseurl, token)

    # Search specifically within the 'Movies' library
    library = plex.library.section(library_name)

    ids = set()

    for movie in library.all():
        # Initialize a variable to hold the ID if found
        imdb_id = None
        
        # Iterate through the external provider IDs
        for guid in movie.guids:
            if 'imdb' in guid.id:
                # guid.id looks like 'imdb://tt0111161'
                # This splits it to get just the 'tt0111161' part
                imdb_id = guid.id.split('://')[-1]
                ids.add(imdb_id)
                
                break

    return ids

def get_movies_library_imdb_ids(library_name: str = 'Films') -> set:
    return get_library_imdb_ids(library_name)

def get_shows_library_imdb_ids(library_name: str = 'Series') -> set:
    return get_library_imdb_ids(library_name)

def is_imdb_id_in_library(imdb_id: str, library_name: str) -> bool:
    ids = get_library_imdb_ids(library_name)
    return imdb_id in ids

def is_movie_imdb_id_in_library(imdb_id: str) -> bool:
    return is_imdb_id_in_library(imdb_id, 'Films')

def is_show_imdb_id_in_library(imdb_id: str) -> bool:
    return is_imdb_id_in_library(imdb_id, 'Series')

