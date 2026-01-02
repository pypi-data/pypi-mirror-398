from playwright.sync_api import sync_playwright
import time
from typing import List, Optional
from pydantic import BaseModel

class TorrentGalaxyContext(BaseModel):
    cookies: Optional[List[dict]]
    screenshot_bytes: Optional[bytes]
    url: str
    headless: bool = True
    domain: str
    torrent_id: str
    wait_seconds: int
    

def get_request_context(headless: bool = True, 
                        domain: str = "torrentgalaxy.to", 
                        torrent_id: str = "16100045",
                        wait_seconds: int = 10) -> TorrentGalaxyContext:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to the URL
        url = f"https://{domain}/torrent/{torrent_id}"
        page.goto(url)

        # Wait for the page to load completely
        time.sleep(wait_seconds)
        
        # Take a screenshot and get the image bytes
        page.set_viewport_size({"width": 1920, "height": 1080})
        screenshot_bytes = page.screenshot(full_page=True)

        # Retrieve cookies
        cookies = context.cookies()

        # Close the browser
        browser.close()
    
    return TorrentGalaxyContext(
        cookies=cookies,
        screenshot_bytes=screenshot_bytes,
        url=url,
        headless=headless,
        domain=domain,
        torrent_id=torrent_id,
        wait_seconds=wait_seconds
    )