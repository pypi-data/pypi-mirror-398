from pathlib import Path
from plexflow.core.storage.object.redis_storage import RedisObjectStore
from typing import Union
import os

class PlexflowObjectStore:
    """A class used to represent the Plexflow Object Store.

    Attributes:
        run_id (str): The run id of the object store.
        host (str): The host of the Redis server. Defaults to 'localhost'.
        port (int): The port of the Redis server. Defaults to 6379.
        db (int): The database index of the Redis server. Defaults to 0.
        default_ttl (int): The default TTL (in seconds) for the stored objects. Defaults to 3600.
        root_key (Union[str, Path]): The root key in the object store. Defaults to "@plexflow".
        bucket_store (RedisObjectStore): The RedisObjectStore instance.
    """

    def __init__(self, run_id: str, host: str = os.getenv('REDIS_HOST', 'localhost'), port: int = int(os.getenv('REDIS_PORT', 6379)), db: int = 0, default_ttl: int = 3600, root_key: Union[str, Path] = "@plexflow", password=os.getenv('REDIS_PASSWORD', None)):
        """Initializes the PlexflowObjectStore with the given parameters.

        Args:
            run_id (str): The run id of the object store.
            host (str, optional): The host of the Redis server. Defaults to 'localhost'.
            port (int, optional): The port of the Redis server. Defaults to 6379.
            db (int, optional): The database index of the Redis server. Defaults to 0.
            default_ttl (int, optional): The default TTL (in seconds) for the stored objects. Defaults to 3600.
            root_key (Union[str, Path], optional): The root key in the object store. Defaults to "@plexflow".
        """

        self.bucket_store = RedisObjectStore(host=host, port=port, db=db, default_ttl=default_ttl, password=password)
        self.root_key = Path(root_key) if isinstance(root_key, str) else root_key
        self.run_id = run_id

    @property
    def bucket(self):
        """Gets the RedisObjectStore instance.

        Returns:
            RedisObjectStore: The RedisObjectStore instance.
        """

        return self.bucket_store

    def make_key(self, name: Union[str, Path]) -> Path:
        """Constructs a global key by joining root_key and name.

        Args:
            name (Union[str, Path]): The name to be joined with root_key.

        Returns:
            Path: The constructed global key.
        """

        if isinstance(name, str):
            name = Path(name)
        return self.root_key / name

    def make_run_key(self, name: Union[str, Path]) -> Path:
        """Constructs a run-specific key by joining root_key, run_id, and name.

        Args:
            name (Union[str, Path]): The name to be joined with root_key and run_id.

        Returns:
            Path: The constructed run-specific key.
        """

        return self.root_key / self.run_id / name

    def store(self, key: Union[str, Path], obj, use_json=False):
        """Stores a serialized version of an object in the Redis store permanently.

        Args:
            key (Union[str, Path]): The key under which the object is stored.
            obj (Any): The object to be stored.
            use_json (bool, optional): Whether to use JSON for serialization. Defaults to False.
        """

        if isinstance(key, Path):
            key = str(key)
        self.bucket_store.store(key, obj, use_json)

    def store_temporarily(self, key: Union[str, Path], obj, ttl=None, use_json=False):
        """Stores a serialized version of an object in the Redis store temporarily.

        Args:
            key (Union[str, Path]): The key under which the object is stored.
            obj (Any): The object to be stored.
            ttl (int, optional): The TTL (in seconds) for the stored object. If not provided, default_ttl is used.
            use_json (bool, optional): Whether to use JSON for serialization. Defaults to False.
        """

        if isinstance(key, Path):
            key = str(key)
        self.bucket_store.store_temporarily(key, obj, ttl, use_json)

    def retrieve(self, key: Union[str, Path], use_json=False):
        """Retrieves an object from the Redis store and deserializes it.

        Args:
            key (Union[str, Path]): The key under which the object is stored.
            use_json (bool, optional): Whether to use JSON for deserialization. Defaults to False.

        Returns:
            Any: The deserialized object.
        """

        if isinstance(key, Path):
            key = str(key)
        return self.bucket_store.retrieve(key, use_json)

    def retrieve_keys(self, pattern):
        """Retrieves all keys matching a given pattern from the Redis store.

        Args:
            pattern (str): The pattern to match.

        Returns:
            list: A list of keys matching the pattern.

        Raises:
            Exception: If an error occurs during retrieving the keys.

        """

        return self.bucket_store.retrieve_keys(pattern)

    def retrieve_values(self, pattern):
        """Retrieves all values matching a given pattern from the Redis store.

        Args:
            pattern (str): The pattern to match.

        Returns:
            list: A list of values matching the pattern.

        Raises:
            Exception: If an error occurs during retrieving the values.

        """

        return self.bucket_store.retrieve_values(pattern)
