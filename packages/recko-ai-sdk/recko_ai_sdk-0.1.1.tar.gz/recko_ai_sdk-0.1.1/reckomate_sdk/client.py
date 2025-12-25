import requests
from typing import Optional


class ReckomateClient:
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json"
        })

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def set_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, params=None):
        return self.session.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout
        )

    def post(self, path: str, json=None, files=None, data=None):
        return self.session.post(
            f"{self.base_url}{path}",
            json=json,
            files=files,
            data=data,
            timeout=self.timeout
        )

    def put(self, path: str, json=None, files=None, data=None):
        return self.session.put(
            f"{self.base_url}{path}",
            json=json,
            files=files,
            data=data,
            timeout=self.timeout
        )

    def delete(self, path: str):
        return self.session.delete(
            f"{self.base_url}{path}",
            timeout=self.timeout
        )
