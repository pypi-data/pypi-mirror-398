from typing import Union, List
from plexflow.core.plex.hooks.plex_authorized import PlexAuthorizedHttpHook
from plexflow.core.plex.api.context.discover import PlexDiscoverRequestContext
from plexflow.core.metadata.providers.plex.datatypes import MovieMediaContainer, PlexMovieMetadata, ShowMediaContainer, PlexShowMetadata, PlexSeasonMetadata, SeasonMediaContainer, PlexEpisodeMetadata, EpisodeMediaContainer, PlexUserState, WatchStateMediaContainer

def search_movie_by_rating_key(key: str) -> Union[PlexMovieMetadata, None]:
    """
    Search for a movie using its rating key.

    Parameters:
    key (str): The rating key of the movie.

    Returns:
    Union[PlexMovieMetadata, None]: A PlexMovieMetadata object containing all the details of the movie.
        None: If the movie is not found or an error occurs.

    Example:
    >>> search_movie_by_rating_key('12345')
    PlexMovieMetadata(title='The Shawshank Redemption', ratingKey='12345', release_date=datetime.datetime(1994, 9, 23, 0, 0), runtime=8520, rating=9.3, votes=2400000, rank=1)
    """
    context = PlexDiscoverRequestContext()
    response = context.get(f"/library/metadata/{key}")
    
    response.raise_for_status()

    data = response.json()

#    import pprint as pp
#    pp.pprint(data.get("MediaContainer"))
    container: MovieMediaContainer = MovieMediaContainer.from_dict(data.get("MediaContainer"))
    
    if len(container.Metadata) > 0:
        return container.Metadata[0]

def search_show_by_rating_key(key: str) -> Union[PlexShowMetadata, None]:
    """
    Search for a show using its rating key.

    Parameters:
    key (str): The rating key of the show.

    Returns:
    Union[PlexShowMetadata, None]: A PlexShowMetadata object containing all the details of the show.
        None: If the show is not found or an error occurs.

    Example:
    >>> search_show_by_rating_key('12345')
    PlexShowMetadata(title='Friends', ratingKey='12345', parentRatingKey='67890')
    """
    context = PlexDiscoverRequestContext()
    response = context.get(f"/library/metadata/{key}")
    
    response.raise_for_status()

    data = response.json()

    container: ShowMediaContainer = ShowMediaContainer.from_dict(data.get("MediaContainer"))
    
    if len(container.Metadata) > 0:
        return container.Metadata[0]


def search_seasons_by_show_rating_key(key: str) -> Union[List[PlexSeasonMetadata], None]:
    """
    Search for seasons of a show using its rating key.

    Parameters:
    key (str): The rating key of the show.

    Returns:
    List[PlexSeasonMetadata]: A list of PlexSeasonMetadata objects containing the details of the seasons.
    None: If the show is not found or an error occurs.

    Example:
    >>> search_seasons_by_show_rating_key('12345')
    [PlexSeasonMetadata(title='Season 1', ratingKey='123', parentRatingKey='456'), PlexSeasonMetadata(title='Season 2', ratingKey='789', parentRatingKey='456')]
    """
    context = PlexDiscoverRequestContext()
    response = context.get(f"/library/metadata/{key}/children")
    
    response.raise_for_status()

    data = response.json()

    container: SeasonMediaContainer = SeasonMediaContainer.from_dict(data.get("MediaContainer"))
    
    if len(container.Metadata) > 0:
        return container.Metadata


def search_episodes_by_season_rating_key(key: str) -> Union[List[PlexEpisodeMetadata], None]:
    """
    Search for episodes of a season using its rating key.

    Parameters:
    key (str): The rating key of the season.

    Returns:
    List[PlexEpisodeMetadata]: A list of PlexEpisodeMetadata objects containing the details of the episodes.
    None: If the season is not found or an error occurs.

    Example:
    >>> search_episodes_by_season_rating_key('12345')
    [PlexEpisodeMetadata(title='Episode 1', duration=3600, rating=8.5), PlexEpisodeMetadata(title='Episode 2', duration=3600, rating=9.0)]
    """
    context = PlexDiscoverRequestContext()
    response = context.get(f"/library/metadata/{key}/children")
    
    response.raise_for_status()

    data = response.json()

    container: EpisodeMediaContainer = EpisodeMediaContainer.from_dict(data.get("MediaContainer"))
    
    if len(container.Metadata) > 0:
        return container.Metadata

def get_all_episodes_by_show_rating_key(key: str) -> List[PlexEpisodeMetadata]:
    """
    Get all episodes of a show using its rating key.

    Parameters:
    key (str): The rating key of the show.

    Returns:
    List[PlexEpisodeMetadata]: A list of PlexEpisodeMetadata objects containing the details of the episodes.

    Example:
    >>> get_all_episodes_by_show_rating_key('12345')
    [PlexEpisodeMetadata(title='Episode 1', duration=3600, rating=8.5), PlexEpisodeMetadata(title='Episode 2', duration=3600, rating=9.0)]
    """
    show = search_show_by_rating_key(key=key)

    seasons = search_seasons_by_show_rating_key(show.ratingKey)

    episodes = []
    for season in seasons:
        tmp = search_episodes_by_season_rating_key(season.ratingKey)
        for x in tmp:
            episodes.append(x)
    return episodes

def get_show_tags(key: str) -> set:
    episodes = get_all_episodes_by_show_rating_key(key=key)

    tags = set()

    for episode in episodes:
        tag = f"s{episode.parentIndex:02d}e{episode.index:02d}"
        tags.add(tag)
    
    return tags

def get_watch_state_by_rating_key(key: str) -> Union[List[PlexUserState], None]:
    """
    Get the watch state of a movie or show using its rating key.

    Parameters:
    key (str): The rating key of the movie or show.

    Returns:
    PlexUserState: A PlexUserState object containing the watch state.
    None: If the movie or show is not found or an error occurs.

    Example:
    >>> get_watch_state_by_rating_key('12345')
    PlexUserState(state='watched', last_viewed_at=datetime.datetime(2022, 1, 1, 0, 0))
    """
    context = PlexDiscoverRequestContext()
    response = context.get(f"/library/metadata/{key}/userState")
    
    response.raise_for_status()

    data = response.json()

    container: WatchStateMediaContainer = WatchStateMediaContainer.from_dict(data.get("MediaContainer"))
    
    return container.UserState
