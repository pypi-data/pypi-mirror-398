from plexflow.core.context.partial_context import PartialContext

class TgxRequestContext(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def update(self, cookies: dict):
        self.set_global("tgx/cookies", cookies)

    @property
    def session_id(self) -> str:
        """
        Cookies is a dictionary like below:
        
        [{'name': 'PHPSESSID', 'value': 'a95el556bo30414fslulnbdi03', 'domain': 'torrentgalaxy.to', 'path': '/', 'expires': -1, 'httpOnly': False, 'secure': False, 'sameSite': 'Lax'}, {'name': 'AdskeeperStorage', 'value': '%7B%220%22%3A%7B%22svspr%22%3A%22https%3A%2F%2Ftorrentgalaxy.to%2Ftorrent%2F16100045%22%2C%22svsds%22%3A2%7D%2C%22C385455%22%3A%7B%22page%22%3A1%2C%22time%22%3A%221722597496754%22%7D%2C%22C1543068%22%3A%7B%22page%22%3A1%2C%22time%22%3A%221722597496757%22%7D%2C%22C1343686%22%3A%7B%22page%22%3A1%2C%22time%22%3A%221722597497305%22%7D%7D', 'domain': 'torrentgalaxy.to', 'path': '/', 'expires': -1, 'httpOnly': False, 'secure': False, 'sameSite': 'Lax'}]
        """
        try:
            cookies = self.get_global("tgx/cookies")
            for cookie in cookies:
                if cookie["name"] == "PHPSESSID":
                    return cookie["value"]
        except Exception:
            return None

    @property
    def cookies(self) -> dict:
        try:
            cookies = self.get_global("tgx/cookies")
            simple_cookies = {}
            for cookie in cookies:
                simple_cookies[cookie["name"]] = cookie["value"]
            return simple_cookies
        except Exception:
            return None