from typing import Optional, Dict, Any
from plexflow.utils.hooks.http import UniversalHttpHook
import requests
from plexflow.core.plex.token.auto_token import PlexAutoToken

class PlexAuthorizedHttpHook(UniversalHttpHook):
    """
    A subclass of UniversalHttpHook that includes the X-Plex-Token as a query parameter.
    
    When used with Airflow, connection details are fetched from Airflow Connections.
    When used standalone, these details should be loaded from a YAML file named after the connection ID.
    
    Args:
        plex_token (str): The Plex token.
        method (str, optional): The HTTP method. Defaults to 'GET'.
        http_conn_id (str, optional): The Airflow connection ID or the name for the YAML file. Defaults to None.
        config_folder (str, optional): The folder where the YAML configuration file is located. Defaults to None.
        
    Attributes:
        hook (HttpHook, optional): The Airflow HttpHook instance.
        session (requests.Session, optional): The requests Session instance.
        config (dict, optional): The configuration loaded from the YAML file.
        
    Examples:
        Using PlexAuthorizedHttpHook with Airflow:
            hook = PlexAuthorizedHttpHook(plex_token='my_plex_token', method='GET', http_conn_id='my_http_connection')
            response = hook.run('/api/v1/resource')
            
        Using PlexAuthorizedHttpHook in standalone mode with a YAML configuration file:
            hook = PlexAuthorizedHttpHook(plex_token='my_plex_token', method='POST', http_conn_id='my_http_connection', config_folder='/path/to/configs')
            response = hook.run('/api/v1/resource', data={'key': 'value'})
    """
    
    def __init__(self, plex_token: str = None, method: str = 'GET', http_conn_id: Optional[str] = None, config_folder: Optional[str] = None):
        super().__init__(method, http_conn_id, config_folder)
        self.plex_token = plex_token

    def run(self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, extra_options: Optional[Dict[str, Any]] = None, query_params: Optional[Dict[str, str]] = None, json: Any = None) -> requests.Response:
        """
        Makes an HTTP request.
        
        Args:
            endpoint (str): The endpoint for the HTTP request.
            data (dict, optional): The data for the HTTP request. Defaults to None.
            headers (dict, optional): The headers for the HTTP request. Defaults to None.
            extra_options (dict, optional): Extra options for the HTTP request. Defaults to None.
            query_params (dict, optional): The query parameters for the HTTP request. Defaults to None.
        
        Returns:
            The response from the HTTP request.
        """
        query_params = query_params or {}
        query_params['X-Plex-Token'] = PlexAutoToken(plex_token=self.plex_token).get_token()
        
        headers = headers or {}
        headers["Accept"] = "application/json"
        
        print(query_params)
        
        return super().run(endpoint=endpoint, data=data, headers=headers, extra_options=extra_options, query_params=query_params, json=json)
