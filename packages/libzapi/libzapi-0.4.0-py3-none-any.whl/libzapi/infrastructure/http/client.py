import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from libzapi.domain.errors import Unauthorized, NotFound, RateLimited


class HttpClient:
    def __init__(self, base_url: str, headers: dict[str, str], timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                **headers,
            }
        )
        retry = Retry(
            total=5,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.timeout = timeout

    def get(self, path: str) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", timeout=self.timeout)
        self._raise(resp)
        return resp.json()

    def post(self, path: str, json: dict) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", json=json, timeout=self.timeout)
        self._raise(resp)
        return resp.json()

    def put(self, path: str, json: dict) -> dict:
        resp = self.session.put(f"{self.base_url}{path}", json=json, timeout=self.timeout)
        self._raise(resp)
        return resp.json()

    def delete(self, path: str) -> None:
        resp = self.session.delete(f"{self.base_url}{path}", timeout=self.timeout)
        self._raise(resp)

    @staticmethod
    def _raise(resp: requests.Response) -> None:
        if resp.status_code == 401:
            raise Unauthorized(resp.text)
        if resp.status_code == 404:
            raise NotFound(resp.text)
        if resp.status_code == 429:
            raise RateLimited(resp.text)
        resp.raise_for_status()
