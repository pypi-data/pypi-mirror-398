import json
import logging
import requests
from slugify import slugify
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

class OpenSubtitles:
    """A class to interact with the OpenSubtitles API."""

    def __init__(self, credentials_path: str, **kwargs):
        """Initialize the OpenSubtitles object with user credentials."""
        self._users = self._parse_credentials(credentials_path)
        if not self._users:
            raise RuntimeError("No user credentials specified")
        self._user_blacklist = set()
        self._update_user_context(**kwargs)

    def _parse_credentials(self, path: str):
        """Parse the credentials from the given file path."""
        with open(path) as fd:
            credentials = json.load(fd)
            return [
                {
                    **{
                        "username": item["login"]["username"],
                        "password": item["login"]["password"]
                    },
                    **{
                        slugify(field["name"].lower(), separator="_", lowercase=True): field["value"]
                        for field in item["fields"]
                    }
                }
                for item in credentials.get("items", [])
            ]

    def _get_user_context(self, **kwargs):
        """Get the user context that is not in the blacklist."""
        ctx = next((ctx for ctx in self._users if ctx["username"] not in self._user_blacklist), None)
        if not ctx:
            raise RuntimeError("No user context available")
        return ctx

    def _update_user_context(self, **kwargs):
        """Update the current user context."""
        self._current_ctx = self._get_user_context(**kwargs)
        payload = {
            "username": self._current_ctx["username"],
            "password": self._current_ctx["password"],
        }
        r = requests.post(
            url="https://api.opensubtitles.com/api/v1/login",
            headers={
                'Content-Type': "application/json",
                'Accept': "application/json",
                'Api-Key': self._current_ctx["api_key"],
                'User-Agent': self._current_ctx["user_agent"],
            },
            data=json.dumps(payload)
        )
        if r.ok:
            response = r.json()
            self._current_ctx["token"] = response.get("token")
        else:
            logging.error(r.text)
            raise RuntimeError("Failed to update user context")

    def get_subtitles(self, **kwargs):
        """Get subtitles from the OpenSubtitles API."""
        r = requests.get(
            url=f"https://api.opensubtitles.com/api/v1/subtitles",
            headers={
                "Api-Key": self._current_ctx["api_key"],
                "User-Agent": self._current_ctx["user_agent"],
            },
            params=kwargs,
        )
        if r.ok:
            return r.json()
        else:
            raise RuntimeError(f"Failed to get subtitles [status={r.status_code}]")

    def get_download_link(self, **kwargs):
        """Get the download link for the given file ID."""
        file_id = kwargs.get("file_id")
        if not isinstance(file_id, int):
            raise RuntimeError("file_id must be of type int")
        r = requests.post(
            url="https://api.opensubtitles.com/api/v1/download",
            headers={
                'Accept': "application/json",
                'Api-Key': self._current_ctx["api_key"],
                "Authorization": f"Bearer {self._current_ctx['token']}",
                "User-Agent": self._current_ctx["user_agent"],
                'Content-Type': "application/json",
            },
            data=json.dumps({
                "file_id": file_id
            })
        )
        if r.ok:
            response = r.json()
            remaining = response["remaining"]
            if remaining <= 0:
                logging.info("Quota reached, updating user context")
                self._user_blacklist.add(self._current_ctx["username"])
                self._update_user_context(**kwargs)
                logging.info("Trying again...")
                return self.get_download_link(**kwargs)
            else:
                return response["link"]
        else:
            logging.error(f"Failed to get download link for file_id={file_id} status={r.status_code}")
            raise RuntimeError(f"Failed to get download link for file_id={file_id} status={r.status_code}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Download subtitles from OpenSubtitles')
    parser.add_argument('--credentials', required=True, help='Path to credentials file')
    args = parser.parse_args()

    oss = OpenSubtitles(credentials_path=args.credentials)
    data = oss.get_subtitles(imdb_id="1375666", languages=",".join(("nl", "en")))

    for sub in data["data"]:
        files = sub["attributes"]["files"]
        for f in files:
            fid = f["file_id"]
            link = oss.get_download_link(file_id=fid)
            for _ in range(100):
                try:
                    r = requests.get(link)
                    if r.ok:
                        with open(f"/Users/david/Downloads/subs/{fid}.srt", "wb") as fd:
                            fd.write(r.content)
                            break
                    else:
                        raise Exception(f"Bad status: {r.status_code}")
                except Exception as e:
                    logging.error(e)
                    time.sleep(0.1)
