import requests
from requests.adapters import HTTPAdapter
from typing import Optional, Dict
import dns.resolver

class DNSHTTPAdapter(HTTPAdapter):
    def __init__(self, dns_servers, *args, **kwargs):
        self.dns_servers = dns_servers
        super().__init__(*args, **kwargs)

    def resolve(self, hostname):
        resolver = dns.resolver.Resolver()
        resolver.nameservers = self.dns_servers
        answers = resolver.resolve(hostname, 'A')
        return [answer.to_text() for answer in answers]

    def send(self, request, **kwargs):
        # Resolve the hostname using the custom DNS servers
        hostname = request.url.split('/')[2].split(':')[0]
        ip_addresses = self.resolve(hostname)
        if ip_addresses:
            request.url = request.url.replace(hostname, ip_addresses[0])
        return super().send(request, **kwargs)

class HttpRequestContext:
    """
    A base class for setting up a default request context for headers, params, etc.

    Args:
        base_url (str): The base URL for the API.
        default_headers (dict, optional): The default headers for the API. Defaults to None.
        default_params (dict, optional): The default parameters for the API. Defaults to None.
        dns_servers (list, optional): A list of DNS servers to use for custom DNS resolution. Defaults to None.

    Attributes:
        session (requests.Session): The requests Session instance.
    """

    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None, default_params: Optional[Dict[str, str]] = None, dns_servers: Optional[list] = None):
        self.session = requests.Session()
        if dns_servers:
            adapter = DNSHTTPAdapter(list(dns_servers))
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
        self.session.headers.update(default_headers or {})
        self.session.params.update(default_params or {})
        self.base_url = base_url
        self.default_headers = default_headers
        self.default_params = default_params

    def get(self, endpoint: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        return self.request('GET', endpoint, headers, params, **kwargs)

    def post(self, endpoint: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        return self.request('POST', endpoint, headers, params, **kwargs)

    def put(self, endpoint: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        return self.request('PUT', endpoint, headers, params, **kwargs)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        return self.request('DELETE', endpoint, headers, params, **kwargs)

    def request(self, method: str, endpoint: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        Makes an HTTP request.
        
        Args:
            method (str): The HTTP method.
            endpoint (str): The endpoint for the HTTP request.
            headers (dict, optional): The headers for the HTTP request. Defaults to None.
            params (dict, optional): The parameters for the HTTP request. Defaults to None.
            **kwargs: Additional arguments passed to requests.Session.request.
        
        Returns:
            The response from the HTTP request.
        """
        if headers:
            self.session.headers.update(headers)
        if params:
            self.session.params.update(params)
        
        response = self.session.request(method, self.base_url + endpoint, **kwargs)
        
        # Reset headers and params to defaults after each request
        self.session.headers = self.default_headers or {}
        self.session.params = self.default_params or {}

        return response
        return response
