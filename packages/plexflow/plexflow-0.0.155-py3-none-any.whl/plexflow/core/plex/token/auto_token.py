import os
import redis
import xml.etree.ElementTree as ET
from typing import Union

class PlexAutoToken:
    """
    A class to automatically try to fetch the value for PLEX_TOKEN from a number of locations.

    This class tries to fetch the Plex token from the following sources in order:
    1. Redis database (optional)
    2. Environment variable 'PLEX_TOKEN'
    3. A Plex configured Preferences.xml file specified by the user
    4. A manually passed token

    If the token is not found in any of these sources, a ValueError is raised.

    Example:
    ```
    plex_token = PlexAutoToken(redis_host='localhost', port=6379, db=0, file_path='/path/to/Preferences.xml').get_token()
    print(plex_token)  # Prints the fetched Plex token
    ```

    Args:
        redis_instance (Union[redis.Redis, None], optional): An instance of a Redis database. Defaults to None.
        redis_host (str, optional): The host of the Redis database. Defaults to 'localhost'.
        port (int, optional): The port of the Redis database. Defaults to 6379.
        db (int, optional): The database index of the Redis database. Defaults to 0.
        file_path (str, optional): The path to the Plex configured Preferences.xml file. Defaults to None.
        plex_token (str, optional): A manually passed Plex token. Defaults to None.
    """

    def __init__(self, redis_instance: Union[redis.Redis, None] = None, redis_host: str = 'localhost', port: int = 6379, db: int = 0, file_path: str = None, plex_token: str = None):
        self.redis_instance = None
        if redis_instance is not None:
            self.redis_instance = redis_instance
        elif redis_host is not None:
            try:
                self.redis_instance = redis.Redis(host=redis_host, port=port, db=db)
            except redis.ConnectionError:
                print("Unable to connect to Redis at {}:{}. Continuing without Redis.".format(redis_host, port))
        self.file_path = file_path
        self.plex_token = plex_token

    def get_token(self) -> str:
        """
        Fetches the Plex token from the sources specified in the class docstring.

        Returns:
            str: The fetched Plex token.

        Raises:
            ValueError: If the Plex token is not found in any of the sources.

        Example:
        ```
        plex_token = PlexAutoToken(redis_host='localhost', port=6379, db=0, file_path='/path/to/Preferences.xml').get_token()
        print(plex_token)  # Prints the fetched Plex token
        ```
        """
        # Try to fetch the token from the Redis instance
        try:
            if self.redis_instance is not None:
                token = self.redis_instance.get('PLEX_TOKEN')
                if token is not None:
                    return token.decode()
        except redis.RedisError as e:
            pass

        # Try to fetch the token from the environment variables
        token = os.getenv('PLEX_TOKEN')
        if token is not None:
            return token

        # Try to fetch the token from the Plex configured Preferences.xml file
        if self.file_path is not None:
            try:
                tree = ET.parse(self.file_path)
                root = tree.getroot()
                token = root.attrib.get('PlexOnlineToken')
                if token:
                    return token
            except FileNotFoundError:
                pass

        # Use the manually passed token
        if self.plex_token is not None:
            return self.plex_token

        # If the token is not found, raise an error
        raise ValueError('PLEX_TOKEN not found')
