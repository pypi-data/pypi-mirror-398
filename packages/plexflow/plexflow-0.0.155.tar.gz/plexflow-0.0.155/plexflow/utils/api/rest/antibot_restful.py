from typing import Optional, Dict
import requests
import plexflow.utils.antibot.human_like_requests as human_like_requests
from urllib.parse import urljoin, urlencode, urlunparse, urlparse
from plexflow.utils.image.storage import upload_image
import logging

class AntibotRestful:
    def __init__(self, base_url: str, use_xvfb: bool = False):
        self._base_url = base_url
        self._use_xvfb = use_xvfb

    def _construct_url(self, path: str, query_params: Optional[Dict[str, str]] = None) -> str:
        # Join the base URL and path
        url = urljoin(self._base_url, path)
        
        # Parse the URL and add query parameters
        url_parts = list(urlparse(url))
        if query_params:
            url_parts[4] = urlencode(query_params)
        return urlunparse(url_parts)

    def get(self, path: str, headers: Optional[Dict[str, str]] = None, query_params: Optional[Dict[str, str]] = None, **kwargs) -> human_like_requests.HumanLikeRequestCapture:
        # Construct the full URL
        url = self._construct_url(path, query_params)
        
        # captures = human_like_requests.get_multiple(
        #     urls=["https://extratorrent.st/search/?new=1&search=twister+2024&s_cat=1", url],
        #     take_screenshot=True,
        #     use_xvfb=self._use_xvfb,
        #     wait_condition=kwargs.get('wait_condition', "regex"),
        #     wait_value=kwargs.get('wait_value', "magnet:"),
        #     wait_until_not=kwargs.get('wait_until_not', False)
        # )
        
        # for capture in captures:
        #     if capture.url == url:
        #         return capture
        
        capture = human_like_requests.get(
            url=url,
            take_screenshot=True,
            use_xvfb=self._use_xvfb,
            wait_condition=kwargs.get('wait_condition', "regex"),
            wait_value=kwargs.get('wait_value', "magnet:"),
            wait_until_not=kwargs.get('wait_until_not', False)
        )
        
        if isinstance(capture.screenshot, bytes):
            try:
                image = capture.screenshot
                image_id = f"{self.url_to_slug(url)}_screenshot"
                details = upload_image(image, public_id=image_id)
                logging.info(f"Uploaded screenshot for {image_id}: {details}")
            except Exception as e:
                logging.error(f"An error occurred while uploading the screenshot for {image_id}: {e}")
    
        return capture
    
    def url_to_slug(self, url: str) -> str:
        # Parse the URL to extract the netloc
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc
        
        # Replace dots in the netloc with hyphens
        slug = netloc.replace('.', '-')
        
        return slug