import os
import yaml
import requests
from typing import Optional, Dict, Any
from airflow.providers.http.hooks.http import HttpHook

class UniversalHttpHook:
    """
    A universal HTTP hook that can work in Airflow as well as standalone.
    
    When used with Airflow, connection details are fetched from Airflow Connections.
    When used standalone, these details should be loaded from a YAML file named after the connection ID.
    
    Args:
        method (str): The HTTP method. Defaults to 'GET'.
        http_conn_id (str, optional): The connection ID, used as Airflow connection ID or as the name for the YAML file. Defaults to None.
        config_folder (str, optional): The folder where the YAML configuration file is located. Defaults to None.
        
    Attributes:
        hook (HttpHook, optional): The Airflow HttpHook instance.
        session (requests.Session, optional): The requests Session instance.
        config (dict, optional): The configuration loaded from the YAML file.
        
    Examples:
        Using UniversalHttpHook with Airflow:
            hook = UniversalHttpHook(method='GET', http_conn_id='my_http_connection')
            response = hook.run('/api/v1/resource')
            
        Using UniversalHttpHook in standalone mode with a YAML configuration file:
            hook = UniversalHttpHook(method='POST', http_conn_id='my_http_connection', config_folder='/path/to/configs')
            response = hook.run('/api/v1/resource', data={'key': 'value'})
    """
    
    def __init__(self, method: str = 'GET', http_conn_id: Optional[str] = None, config_folder: Optional[str] = None):
        self.method = method
        self.http_conn_id = http_conn_id
        self.config_folder = '' if config_folder is None else config_folder
        if not self.config_folder:
            self.hook = HttpHook(http_conn_id=self.http_conn_id, method=self.method)
        else:
            self.hook = None
            if self.http_conn_id is None:
                raise ValueError("http_conn_id must be provided when running in standalone mode")
            self.session = requests.Session()
            config_path = os.path.join(self.config_folder, f"{self.http_conn_id}.yaml")
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)

    def get_conn(self, headers: Dict[str, str]) -> Any:
        """
        Establishes a connection for making HTTP requests.
        
        Args:
            headers (dict): The headers for the HTTP request.
            
        Returns:
            An object that can be used to make HTTP requests.
        """
        if self.hook:
            return self.hook.get_conn(headers)
        else:
            self.session.headers.update(self.config['headers'])
            return self.session

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
        if self.hook:
            return self.hook.run(endpoint, data, headers, extra_options, query_params, json=json)
        else:
            url = self.config['base_url'] + endpoint
            response = self.session.request(self.method, url, data=data, headers=headers, params=query_params, json=json)
            return response
