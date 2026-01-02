from plexflow.core.plex.api.context.authorized import PlexAuthorizedRequestContext
from plexflow.core.plex.token.auto_token import PlexAutoToken
import os

class PlexLibraryRequestContext(PlexAuthorizedRequestContext):
    """
    A class for setting up a default request context for Plex Library API with X-Plex-Token header.
    """

    def __init__(self, base_url: str = None, x_plex_token: str = None):
        # Initialize the parent class with the base_url and default_headers
        super().__init__(base_url or f'http://{os.getenv("PLEX_HOST")}:{os.getenv("PLEX_PORT", 32400)}', 
                         {'X-Plex-Token': PlexAutoToken(plex_token=x_plex_token).get_token(), 
                          'Accept': 'application/json'})
