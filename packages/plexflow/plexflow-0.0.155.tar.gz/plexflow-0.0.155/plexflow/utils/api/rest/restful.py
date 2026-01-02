from typing import Optional, Dict, Any
import requests
from plexflow.utils.api.context.http import HttpRequestContext

class Restful:
    """
    A class that uses UniversalHttpHook and UniversalPostgresqlHook to create RESTful API interfaces and interact with a PostgreSQL database.
    
    Args:
        http_conn_id (str, optional): The connection ID, used as Airflow connection ID or as the name for the YAML file. Defaults to None.
        postgres_conn_id (str, optional): The connection ID, used as Airflow connection ID or as the name for the YAML file. Defaults to None.
        config_folder (str, optional): The folder where the YAML configuration file is located. Defaults to None.
    """
    
    def __init__(self, base_url: str):
        self._base_url = base_url

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, query_params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        Makes a GET request to the resource.
        
        Args:
            url (str): The full URL for the GET request.
            headers (dict, optional): The headers for the GET request. Defaults to None.
            query_params (dict, optional): The query parameters for the GET request. Defaults to None.
            **kwargs: Additional keyword arguments for the GET request.
        
        Returns:
            The response from the GET request.
        """
        context = HttpRequestContext(self._base_url)
        return context.get(url, headers=headers, params=query_params, **kwargs)

    def post(self, url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None, query_params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        Makes a POST request to the resource.
        
        Args:
            url (str): The full URL for the POST request.
            data (dict): The data for the POST request.
            headers (dict, optional): The headers for the POST request. Defaults to None.
            query_params (dict, optional): The query parameters for the POST request. Defaults to None.
            **kwargs: Additional keyword arguments for the POST request.
        
        Returns:
            The response from the POST request.
        """
        context = HttpRequestContext(self._base_url)
        return context.post(url, headers=headers, params=query_params, **kwargs)
