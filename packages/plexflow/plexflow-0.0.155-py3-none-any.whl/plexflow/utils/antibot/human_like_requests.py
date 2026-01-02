import subprocess
import time
import os
import logging
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from seleniumbase import SB
from bs4 import BeautifulSoup
import json

class HumanLikeRequestCapture:
    def __init__(self, url, html, screenshot, cookies):
        self.url = url
        self.html = html
        self.screenshot = screenshot
        self.cookies = cookies

    @property
    def json(self):
        try:
            soup = BeautifulSoup(self.html, 'html.parser')
            return json.loads(soup.get_text())
        except json.decoder.JSONDecodeError:
            return None
        
class HumanLikeRequestSession:
    def __init__(self, use_xvfb=False):
        self.use_xvfb = use_xvfb
        if self.use_xvfb:
            self._start_xvfb()

    def _start_xvfb(self):
        self.xvfb_process = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
        logging.info("Xvfb started")
        time.sleep(5)
        os.environ['DISPLAY'] = ':99'

    def _stop_xvfb(self):
        if self.xvfb_process:
            self.xvfb_process.terminate()
            logging.info("Xvfb terminated")

    def execute_requests(self, urls: iter, take_screenshot: bool = False, wait_condition: str = "element", wait_value: str = "content", wait_until_not: bool = False, max_retries: int = 3) -> iter:
        with SB(uc=True, maximize=True, test=False, headed=True, incognito=True, chromium_arg="--disable-search-engine-choice-screen") as sb:
            logging.info("Running test task")
            for url in urls:
                cookies = None
                for attempt in range(max_retries):
                    logging.info(f"[{attempt}/{max_retries}] Opening URL")
                    sb.uc_open_with_reconnect(url, 10)
                    sb.uc_gui_click_cf()
                    cookies = sb.get_cookies()
                    logging.info(cookies)

                    # Wait for a specific condition instead of sleeping
                    try:
                        if wait_condition == "element":
                            if wait_until_not:
                                WebDriverWait(sb.driver, 20).until_not(
                                    EC.presence_of_element_located((By.ID, wait_value))
                                )
                            else:
                                WebDriverWait(sb.driver, 20).until(
                                    EC.presence_of_element_located((By.ID, wait_value))
                                )
                        elif wait_condition == "regex":
                            if wait_until_not:
                                WebDriverWait(sb.driver, 20).until_not(
                                    lambda driver: re.search(wait_value, driver.page_source)
                                )
                            else:
                                WebDriverWait(sb.driver, 20).until(
                                    lambda driver: re.search(wait_value, driver.page_source)
                                )
                        elif wait_condition == "custom":
                            result = [None]  # Use a list to store the result
                            if wait_until_not:
                                WebDriverWait(sb.driver, 20).until_not(
                                    lambda driver: (result.__setitem__(0, wait_value(driver)) or result[0])
                                )
                            else:
                                WebDriverWait(sb.driver, 20).until(
                                    lambda driver: (result.__setitem__(0, wait_value(driver)) or result[0])
                                )

                            print("Result:", result[0])

                            if result[0] == "retry":
                                continue
                    except TimeoutException:
                        logging.warning("Wait condition not met within the timeout period.")
                    
                    break
            
                if take_screenshot:
                    logging.info("Taking screenshot")
                    screenshot = sb.driver.get_screenshot_as_png()
                else:
                    screenshot = None

                html = sb.get_page_source()
                
                # Assuming HumanLikeRequestCapture is the response object
                yield HumanLikeRequestCapture(url=url, html=html, screenshot=screenshot, cookies=cookies)

    def execute_request(self, url: str, take_screenshot: bool = False, wait_condition: str = "element", wait_value: str = "content", wait_until_not: bool = False) -> HumanLikeRequestCapture:
        return next(self.execute_requests([url], take_screenshot, wait_condition, wait_value, wait_until_not))

    def close(self):
        if self.use_xvfb:
            self._stop_xvfb()

def get(url: str, take_screenshot: bool = False, use_xvfb: bool = False, wait_condition: str = "element", wait_value: str = "content", wait_until_not: bool = False) -> HumanLikeRequestCapture:
    session = HumanLikeRequestSession(use_xvfb=use_xvfb)
    try:
        response = session.execute_request(url=url, take_screenshot=take_screenshot, wait_condition=wait_condition, wait_value=wait_value, wait_until_not=wait_until_not)
        response.use_xvfb = use_xvfb
        return response
    finally:
        session.close()

def get_multiple(urls: iter, take_screenshot: bool = False, use_xvfb: bool = False, wait_condition: str = "element", wait_value: str = "content", wait_until_not: bool = False) -> iter:
    session = HumanLikeRequestSession(use_xvfb=use_xvfb)
    try:
        for response in session.execute_requests(urls=urls, take_screenshot=take_screenshot, wait_condition=wait_condition, wait_value=wait_value, wait_until_not=wait_until_not):
            response.use_xvfb = use_xvfb
            yield response
    finally:
        session.close()
