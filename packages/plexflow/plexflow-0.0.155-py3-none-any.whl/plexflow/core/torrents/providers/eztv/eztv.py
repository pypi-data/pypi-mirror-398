from plexflow.utils.api.rest.restful import Restful
from plexflow.core.torrents.providers.eztv.utils import EZTVSearchResult

class EZTV(Restful):
    """EZTV class to interact with the EZTV API.

    This class inherits from the Restful class and provides an interface to
    interact with the EZTV API. It provides a method to search for torrents
    using an IMDb ID.

    Attributes:
        http_conn_id (str): The connection ID for the HTTP connection.
        config_folder (str): The folder where the configuration files are stored.
    """

    def __init__(self, base_url: str = 'https://eztv.re'):
        """Initializes EZTV with the given HTTP connection ID and config folder."""
        super().__init__(base_url=base_url)
    
    def search(self, imdb_id: str):
        """Searches for torrents using an IMDb ID.

        This method takes an IMDb ID as input, normalizes it by removing the
        leading 'tt' and any leading zeros, and then makes a GET request to
        the EZTV API to search for torrents. It raises an exception if the
        response status is not OK, and returns a list of EZTVSearchResult
        objects if the response is OK.

        Args:
            imdb_id (str): The IMDb ID to search for.

        Returns:
            list[EZTVSearchResult]: A list of EZTVSearchResult objects.
        """
        # Normalize the imdb_id by removing leading 'tt' and zeros
        imdb_id = imdb_id.lstrip('tt')

        response = self.get(url='/api/get-torrents', query_params={
            'imdb_id': imdb_id,
        })
        
        response.raise_for_status()
        
        # TODO pagination
        data = response.json()
        
        return list(map(lambda x: EZTVSearchResult(**x), data.get("torrents", [])))
