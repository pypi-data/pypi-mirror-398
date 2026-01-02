import redis
import yaml
from typing import List, Dict, Optional, Iterator
from contextlib import contextmanager
from datetime import datetime
from plexflow.core.subtitles.providers.oss.oss import OpenSubtitles
from plexflow.core.subtitles.providers.oss.utils.exceptions import OpenSubtitlesDownloadQuotaReachedException
from plexflow.core.subtitles.providers.oss.utils.download_client import DownloadClient
from plexflow.core.subtitles.providers.oss.utils.languages import language_codes
from plexflow.core.subtitles.providers.oss.utils.responses import SearchResponse, Subtitle, DiscoverLatestResponse, DiscoverMostDownloadedResponse
import logging
import hashlib
import json
import logging
from plexflow.utils.hooks.redis import UniversalRedisHook
from plexflow.logging.log_setup import logger

class OpenSubtitlesManager:
    """
    A manager class for interacting with the OpenSubtitles API.

    This class provides a convenient way to manage multiple credentials and handle the rate limits of the OpenSubtitles API.
    It allows you to create an instance of the OpenSubtitles class using a valid credential, and automatically handles
    credential rotation and blacklisting.

    Usage:
    credentials = [
        {
            'user_agent': 'UserAgent1',
            'api_key': 'APIKey1',
            'username': 'Username1',
            'password': 'Password1'
        },
        {
            'user_agent': 'UserAgent2',
            'api_key': 'APIKey2',
            'username': 'Username2',
            'password': 'Password2'
        }
    ]

    with OpenSubtitlesManager(credentials) as instance:
        # Use the instance to make API calls
        subtitles = instance.search_subtitles(...)

    Args:
        credentials (List[Dict[str, str]]): A list of dictionaries containing the credentials for accessing the OpenSubtitles API.
            Each dictionary should contain the following keys: 'user_agent', 'api_key', 'username', 'password'.
        redis_host (str, optional): The host of the Redis server used for blacklisting credentials. Defaults to 'localhost'.
        redis_port (int, optional): The port of the Redis server used for blacklisting credentials. Defaults to 6379.
    """
    REDIS_KEY_PREFIX = "blacklist"
    REDIS_DEFAULT_PORT = 6379
    DEFAULT_TTL = 60*60  # 1 hour

    def __init__(self, credentials: List[Dict[str, str]], r: redis.Redis = None, **kwargs):
        """
        Initializes an instance of the OpenSubtitlesManager class.

        Args:
            credentials (List[Dict[str, str]]): A list of dictionaries containing the credentials for accessing the OpenSubtitles API.
                Each dictionary should contain the following keys: 'user_agent', 'api_key', 'username', 'password'.
            redis_host (str, optional): The host of the Redis server used for blacklisting credentials. Defaults to 'localhost'.
            redis_port (int, optional): The port of the Redis server used for blacklisting credentials. Defaults to 6379.
        """
        self.credentials = credentials
        self.redis = r
        self.current_instance = None
        self.current_credential = None
        self.ignore_blacklist = kwargs.get('ignore_blacklist', False)
        self.logger = logger
        self.instances = {}
        
    @classmethod
    def from_yaml(cls, yaml_file: str, r: redis.Redis = None, **kwargs) -> 'OpenSubtitlesManager':
        """
        Creates an instance of the OpenSubtitlesManager class from a YAML file.

        Args:
            yaml_file (str): The path to the YAML file containing the credentials.
            redis_host (str, optional): The host of the Redis server used for blacklisting credentials. Defaults to 'localhost'.
            redis_port (int, optional): The port of the Redis server used for blacklisting credentials. Defaults to 6379.

        Returns:
            OpenSubtitlesManager: The created instance of the OpenSubtitlesManager class.
        """
        print("YAML:", yaml_file)
        with open(yaml_file, 'r') as file:
            credentials = yaml.safe_load(file)
        return cls(credentials=credentials, r=r, **kwargs)

    def __enter__(self) -> OpenSubtitles:
        """
        Enters the context and returns a valid instance of the OpenSubtitles class.

        This context manager handles credential rotation and blacklisting.
        If a OpenSubtitlesDownloadQuotaReachedException is raised inside the context manager,
        the current credential will be blacklisted for a certain duration (default is 60 seconds)
        and the exception will be re-raised.

        Returns:
            OpenSubtitles: The current valid instance of the OpenSubtitles class.
        """
        self.current_credential = self.get_next_available_credential()
        self.current_instance = self.create_open_subtitles_instance(self.current_credential)
        return self.current_instance

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the context and cleans up the current instance and credential.

        Args:
            exc_type: The type of the exception raised, if any.
            exc_value: The exception raised, if any.
            traceback: The traceback of the exception raised, if any.
        """
        if exc_type == OpenSubtitlesDownloadQuotaReachedException:
            self.blacklist_credential()
            self.logger.warning(f"OpenSubtitlesDownloadQuotaReachedException occurred. Credential blacklisted for {self.DEFAULT_TTL} seconds.")
            self.current_instance = None
            self.current_credential = None
            return False  # Re-raise the exception

        self.current_instance = None
        self.current_credential = None


    def get_next_available_credential(self) -> Dict[str, str]:
        """
        Returns the next available credential from the list of credentials.

        Raises:
            Exception: If no available credentials are found.

        Returns:
            Dict[str, str]: The next available credential.
        """
        for credential in self.credentials["items"]:
            login = credential.get('login', {})
            username = login.get('username')
            password = login.get('password')
            fields = credential.get('fields', [])
            api_key = None
            user_agent = None
            for field in fields:
                if field['name'] == 'API Key':
                    api_key = field['value']
                elif field['name'] == 'User Agent':
                    user_agent = field['value']
            
            credential_data = {
                'username': username,
                'password': password,
                'api_key': api_key,
                'user_agent': user_agent
            }
            
            if self.ignore_blacklist or not self.is_credential_blacklisted(credential_data):
                return credential_data

        self.logger.error("No available credentials found")
        raise Exception("No available credentials found")

    def create_open_subtitles_instance(self, credential: Dict[str, str]) -> OpenSubtitles:
        """
        Creates an instance of the OpenSubtitles class using the given credential.

        Args:
            credential (Dict[str, str]): The credential to use for creating the instance.

        Returns:
            OpenSubtitles: The created instance of the OpenSubtitles class.
        """
        api_key = credential.get('api_key')
        user_agent = credential.get('user_agent')
        username = credential.get('username')
        password = credential.get('password')
        
        self.logger.debug(f"Username: {username}, User Agent: {user_agent}")
        
        # Check if instance already exists for the given credential
        if api_key in self.instances:
            return self.instances[api_key]
        
        instance = OpenSubtitles(user_agent, api_key, r=self.redis)
        instance.login(username, password)
        
        # Cache the instance for later reuse
        self.instances[api_key] = instance
        
        return instance

    def is_credential_blacklisted(self, credential: Dict[str, str]) -> bool:
        """
        Checks if the given credential is blacklisted.

        Args:
            credential (Dict[str, str]): The credential to check.

        Returns:
            bool: True if the credential is blacklisted, False otherwise.
        """
        key = self.generate_credential_key(credential)
        self.logger.debug(f"Generated credential key: {key}")
        return self.redis.exists(key)

    def blacklist_credential(self):
        """
        Blacklists the current credential for the specified duration.

        """
        key = self.generate_credential_key(self.current_credential)
        self.redis.setex(key, self.DEFAULT_TTL, 'blacklisted')
        self.logger.debug(f"Credential blacklisted for {self.DEFAULT_TTL} seconds: {self.current_credential}")
        self.logger.debug(f"Blacklisted credential key: {key}")

    def generate_credential_key(self, credential: Dict[str, str]) -> str:
        """
        Generates the key for the given credential.

        Args:
            credential (Dict[str, str]): The credential to generate the key for.

        Returns:
            str: The generated key.
        """
        credential_sorted = json.dumps(credential, sort_keys=True)
        key_parts = [
            self.REDIS_KEY_PREFIX,
            hashlib.sha256(credential_sorted.encode()).hexdigest()
        ]
        return ":".join(key_parts)
