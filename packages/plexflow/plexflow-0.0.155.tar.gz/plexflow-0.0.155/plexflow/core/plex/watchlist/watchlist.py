from plexflow.core.plex.hooks.plex_authorized import PlexAuthorizedHttpHook
from plexflow.core.plex.watchlist.datatypes import from_json, MediaContainer
from plexflow.core.plex.utils.paginated import paginated
from plexflow.core.plex.api.context.authorized import PlexAuthorizedRequestContext

@paginated
def get_watchlist(**kwargs) -> MediaContainer:
    """
    Retrieves the watchlist from the Plex server.

    Args:
        **kwargs: Additional keyword arguments to be passed to the PlexAuthorizedHttpHook.

    Returns:
        MediaContainer: The watchlist as a MediaContainer object. 
        
    Raises:
        None

    """
    context = PlexAuthorizedRequestContext(base_url="https://discover.provider.plex.tv")
    response = context.get(endpoint="/library/sections/watchlist/all", **kwargs)
    return from_json(response.content.decode("utf-8"))