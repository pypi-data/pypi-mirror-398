import requests
from typing import Optional, Dict, Any


class ReckomateClient:
    """
    Core HTTP client for Reckomate SDK.
    This client is used by:
    1) Normal SDK service calls
    2) Gateway proxy projects (SDK-ONLY enforcement)
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: int = 60
    ):
        if not base_url:
            raise ValueError("base_url is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "reckomate-sdk/1.0.7"
        })

        if token:
            self.set_token(token)

    # ======================================================
    # 🔐 AUTH
    # ======================================================

    def set_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"

    # ======================================================
    # ✅ STANDARD SDK METHODS
    # ======================================================

    def get(self, path: str, params: Dict[str, Any] | None = None):
        return self.session.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout
        )

    def post(
        self,
        path: str,
        json: Dict[str, Any] | None = None,
        files=None,
        data=None
    ):
        return self.session.post(
            f"{self.base_url}{path}",
            json=json,
            files=files,
            data=data,
            timeout=self.timeout
        )

    def put(
        self,
        path: str,
        json: Dict[str, Any] | None = None,
        files=None,
        data=None
    ):
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

    # ======================================================
    # 🔥 GATEWAY PROXY METHOD (VERY IMPORTANT)
    # ======================================================

    def proxy_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str] | None = None,
        body: bytes | None = None,
        params: Dict[str, Any] | None = None,
    ):
        """
        LOW-LEVEL request used by gateway projects.
        This makes SDK mandatory for proxy routing.
        """

        # Start with SDK session headers
        req_headers = dict(self.session.headers)

        # Merge incoming headers (gateway identity etc.)
        if headers:
            req_headers.update(headers)

        response = self.session.request(
            method=method.upper(),
            url=f"{self.base_url}{path}",
            headers=req_headers,
            params=params,
            data=body,
            timeout=self.timeout
        )

        return response
