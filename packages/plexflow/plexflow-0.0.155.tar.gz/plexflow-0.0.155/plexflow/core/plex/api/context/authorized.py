from plexflow.utils.api.context.http import HttpRequestContext
from plexflow.core.plex.token.auto_token import PlexAutoToken

class PlexAuthorizedRequestContext(HttpRequestContext):
    """
    A class for setting up a default request context for Plex API with X-Plex-Token header.
    
    Args:
        base_url (str): The base URL for the Plex API.
        x_plex_token (str): The X-Plex-Token for the Plex API.
    """
    
    def __init__(self, base_url: str, x_plex_token: str = None):
        # Initialize the parent class with the base_url and default_headers
        super().__init__(base_url, {'X-Plex-Token': PlexAutoToken(plex_token=x_plex_token).get_token(), 'Accept': 'application/json'})
