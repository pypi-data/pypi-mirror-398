import json
import pickle
import redis

class RedisObjectStore:
    """A class used to represent a Redis Object Store.

    Attributes:
        client (Redis): A Redis client instance.
        default_ttl (int): The default TTL (in seconds) for stored objects.

    """

    def __init__(self, host='localhost', port=6379, db=0, default_ttl=3600, password=None):
        """Constructs all the necessary attributes for the RedisObjectStore object.

        Args:
            host (str, optional): The host of the Redis server. Defaults to 'localhost'.
            port (int, optional): The port of the Redis server. Defaults to 6379.
            db (int, optional): The database index of the Redis server. Defaults to 0.
            default_ttl (int, optional): The default TTL (in seconds) for stored objects. Defaults to 3600.

        """

        self.client = redis.Redis(host=host, port=port, db=db, password=password)
        self.default_ttl = default_ttl

    def _serialize(self, obj, use_json=False):
        """Serializes an object.

        Args:
            obj (object): The object to serialize.
            use_json (bool, optional): Whether to use JSON for serialization. If False, pickle is used.

        Returns:
            str: The serialized object.

        Raises:
            Exception: If an error occurs during serialization.

        """

        try:
            return json.dumps(obj) if use_json else pickle.dumps(obj)
        except (TypeError, pickle.PicklingError) as e:
            raise Exception("Failed to serialize object") from e

    def retrieve_keys(self, pattern):
        """Retrieves all keys matching a given pattern from the Redis store.

        Args:
            pattern (str): The pattern to match.

        Returns:
            list: A list of keys matching the pattern.

        Raises:
            Exception: If an error occurs during retrieving the keys.

        """

        try:
            keys = self.client.keys(str(pattern))
            return keys
        except redis.RedisError as e:
            raise Exception("Failed to retrieve keys from Redis") from e

    def retrieve_values(self, pattern, use_json=False):
        """Retrieves all values matching a given pattern from the Redis store and deserializes them.

        Args:
            pattern (str): The pattern to match.
            use_json (bool, optional): Whether to use JSON for deserialization. If False, pickle is used.

        Returns:
            list: A list of deserialized values matching the pattern.

        Raises:
            Exception: If an error occurs during retrieving or deserializing the values.

        """

        try:
            keys = self.client.keys(str(pattern))
            serialized_values = self.client.mget(keys)
            values = []
            for serialized_value in serialized_values:
                if serialized_value is not None:
                    value = json.loads(serialized_value) if use_json else pickle.loads(serialized_value)
                    values.append(value)
                else:
                    values.append(None)
            return values
        except redis.RedisError as e:
            raise Exception("Failed to retrieve values from Redis") from e

    def _store(self, key, serialized_object, ttl=None):
        """Stores a serialized object in the Redis store.

        Args:
            key (str): The key under which the object is stored.
            serialized_object (str): The serialized object to store.
            ttl (int, optional): The TTL (in seconds) for the stored object. If None, the object is stored permanently.

        Raises:
            Exception: If an error occurs during storing the object.

        """

        try:
            self.client.set(key, serialized_object, ex=ttl)
        except redis.RedisError as e:
            raise Exception("Failed to store object in Redis") from e

    def store(self, key, obj, use_json=False):
        """Stores a serialized version of an object in the Redis store permanently.

        Args:
            key (str): The key under which the object is stored.
            obj (object): The object to store.
            use_json (bool, optional): Whether to use JSON for serialization. If False, pickle is used.

        """

        serialized_object = self._serialize(obj, use_json)
        self._store(key, serialized_object)

    def store_temporarily(self, key, obj, ttl=None, use_json=False):
        """Stores a serialized version of an object in the Redis store temporarily.

        Args:
            key (str): The key under which the object is stored.
            obj (object): The object to store.
            ttl (int, optional): The TTL (in seconds) for the stored object. If None, the default TTL is used.
            use_json (bool, optional): Whether to use JSON for serialization. If False, pickle is used.

        """

        serialized_object = self._serialize(obj, use_json)
        ttl = self.default_ttl if ttl is None else ttl
        self._store(key, serialized_object, ttl)

    def retrieve(self, key, use_json=False):
        """Retrieves an object from the Redis store and deserializes it.

        Args:
            key (str): The key of the object to retrieve.
            use_json (bool, optional): Whether to use JSON for deserialization. If False, pickle is used.

        Returns:
            object: The retrieved and deserialized object. If the object does not exist, returns None.

        Raises:
            Exception: If an error occurs during retrieving or deserializing the object.

        """

        try:
            serialized_object = self.client.get(key)
        except redis.RedisError as e:
            raise Exception("Failed to retrieve object from Redis") from e

        if serialized_object is None:
            return None

        try:
            return json.loads(serialized_object) if use_json else pickle.loads(serialized_object)
        except (json.JSONDecodeError, pickle.UnpicklingError) as e:
            raise Exception("Failed to deserialize object") from e
