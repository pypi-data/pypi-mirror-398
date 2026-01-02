import os
import yaml
import redis
from typing import Optional, Dict, Any
from airflow.providers.redis.hooks.redis import RedisHook

class UniversalRedisHook:
    """
    A universal Redis hook that can work in Airflow as well as standalone.
    
    When used with Airflow, connection details are fetched from Airflow Connections.
    When used standalone, these details should be loaded from a YAML file named after the connection ID.
    
    Args:
        redis_conn_id (str, optional): The connection ID, used as Airflow connection ID or as the name for the YAML file. Defaults to None.
        config_folder (str, optional): The folder where the YAML configuration file is located. Defaults to None.
        
    Attributes:
        hook (RedisHook, optional): The Airflow RedisHook instance.
        redis_client (redis.Redis, optional): The Redis client instance.
        config (dict, optional): The configuration loaded from the YAML file.
        
    Examples:
        Using UniversalRedisHook with Airflow:
            hook = UniversalRedisHook(redis_conn_id='my_redis_connection')
            response = hook.run('GET', 'my_key')
            
        Using UniversalRedisHook in standalone mode with a YAML configuration file:
            hook = UniversalRedisHook(redis_conn_id='my_redis_connection', config_folder='/path/to/configs')
            response = hook.run('SET', 'my_key', 'my_value')
    """
    
    def __init__(self, redis_conn_id: Optional[str] = None, config_folder: Optional[str] = None):
        self.redis_conn_id = redis_conn_id
        self.config_folder = '' if config_folder is None else config_folder
        if not self.config_folder:
            self.hook = RedisHook(redis_conn_id=self.redis_conn_id)
        else:
            self.hook = None
            if self.redis_conn_id is None:
                raise ValueError("redis_conn_id must be provided when running in standalone mode")
            config_path = os.path.join(self.config_folder, f"{self.redis_conn_id}.yaml")
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            self.redis_client = redis.Redis(**self.config)

    def get_conn(self) -> Any:
        """
        Establishes a connection to Redis.
        
        Returns:
            An object that can be used to interact with Redis.
        """
        if self.hook:
            return self.hook.get_conn()
        else:
            return self.redis_client

    def run(self, command: str, *args, **kwargs) -> Any:
        """
        Executes a Redis command.
        
        Args:
            command (str): The Redis command to execute.
            *args: Positional arguments for the Redis command.
            **kwargs: Keyword arguments for the Redis command.
        
        Returns:
            The result of the Redis command.
        """
        if self.hook:
            return self.hook.run(command, *args, **kwargs)
        else:
            return getattr(self.redis_client, command)(*args, **kwargs)

    def get(self, key: str) -> Optional[str]:
        """
        Get the value of a key.

        Args:
            key (str): The key to retrieve.

        Returns:
            The value associated with the key, or None if the key does not exist.
        """
        if self.hook:
            return self.hook.get_conn().get(key)
        else:
            return self.redis_client.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set the value of a key.

        Args:
            key (str): The key to set.
            value (str): The value to associate with the key.
            expiration (int, optional): The expiration time in seconds. Defaults to None.

        Returns:
            True if the key was set successfully, False otherwise.
        """
        if self.hook:
            if ex is None:
                return self.hook.get_conn().set(key, value)
            else:
                return self.hook.get_conn().set(key, value, ex=ex)
        else:
            if ex is None:
                return self.redis_client.set(key, value)
            else:
                return self.redis_client.set(key, value, ex=ex)
