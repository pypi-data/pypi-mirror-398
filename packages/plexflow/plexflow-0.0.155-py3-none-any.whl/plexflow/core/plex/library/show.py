from plexapi.server import PlexServer
import os

class PlexLibraryShow:
    def __init__(self, guid: str, plex_host: str = os.getenv('PLEX_HOST'), 
                 plex_port: int = int(os.getenv('PLEX_PORT', 32400)),
                 plex_token: str = os.getenv('PLEX_TOKEN')):
        self.BASEURL = f'http://{plex_host}:{plex_port}'  # e.g., 'http://192.168.1.100:32400'
        self.PLEX_TOKEN = plex_token
        self.guid = guid

        try:
            self.plex = PlexServer(self.BASEURL, self.PLEX_TOKEN)
            print("Successfully connected to Plex using direct URL and token.")
        except Exception as e:
            print(f"Error connecting to Plex with direct URL/token: {e}")
    
        try:
            # 1. Access the TV Shows library
            tv_shows_library = self.plex.library.section('Series')

            # 2. Search the library, filtering by the GUID
            # The 'guid' parameter in search can be used to filter by the item's GUID.
            # It returns a list, as theoretically multiple items could have the same GUID (though rare for primary GUIDs).
            found_shows = tv_shows_library.search(guid=self.guid)

            if found_shows:
                # Assuming the first result is the one we want (often the case for unique GUIDs)
                show = found_shows[0]

                if show.TYPE == 'show':
                    self._show = show
                    print(f"\nFound show by GUID '{self.guid}': {show.title}")
                    print(f"Rating Key: {show.ratingKey}")
                    print(f"Summary: {show.summary[:100]}...")
                else:
                    raise RuntimeError(f"Item with GUID '{self.guid}' is not a TV show (it's a {show.TYPE}).")
            else:
                raise RuntimeError(f"No show found with GUID: {self.guid}")

        except Exception as e:
            raise RuntimeError(f"An error occurred while fetching item by GUID {self.guid}: {e}")
    
    @property
    def show(self):
        return self._show
    
    @property
    def tags(self):
        show = self.show

        tags = set()
        
        seasons = show.seasons()
        if seasons:
            for season in seasons:
                episodes = season.episodes()
                if episodes:
                    for episode in episodes:
                        tag = f"s{season.index:02d}e{episode.index:02d}"
                        tags.add(tag)
                else:
                    print(f"    No episodes found for Season {season.index}.")
        else:
            print(f"No seasons found for '{show.title}'.")
        
        return tags