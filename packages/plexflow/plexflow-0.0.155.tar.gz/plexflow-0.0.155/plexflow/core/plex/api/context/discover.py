from plexflow.core.plex.api.context.authorized import PlexAuthorizedRequestContext
from plexflow.core.plex.token.auto_token import PlexAutoToken
import os

class PlexDiscoverRequestContext(PlexAuthorizedRequestContext):
    """
    A class for setting up a default request context for Plex Discover API with X-Plex-Token header.
    """

    def __init__(self, base_url: str = None, x_plex_token: str = None):
        # Initialize the parent class with the base_url and default_headers
        super().__init__(base_url or f'https://discover.provider.plex.tv', 
                         {'X-Plex-Token': PlexAutoToken(plex_token=x_plex_token).get_token(), 
                          'Accept': 'application/json'})
