from pathlib import Path
from typing import Dict, Optional

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class AdminService:
    """
    Admin SDK Service

    Handles:
    - Admin registration
    - Admin login
    - Admin document/audio/video ingest
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ============================================================
    # AUTH
    # ============================================================

    def register(self, email: str, password: str) -> Dict:
        """
        Register a new admin.

        Backend: POST /admin/register
        """
        payload = {
            "email": email,
            "password": password
        }

        response = self.client.post("/admin/register", json=payload)
        return self._handle_response(response)

    def login(self, email: str, password: str) -> Dict:
        """
        Login admin.

        Backend: POST /admin/login
        """
        payload = {
            "email": email,
            "password": password
        }

        response = self.client.post("/admin/login", json=payload)
        return self._handle_response(response)

    # ============================================================
    # INGEST
    # ============================================================

    def ingest_file(
        self,
        file_path: str,
        admin_id: Optional[str] = None
    ) -> Dict:
        """
        Upload & ingest a document/audio/video file.

        Backend: POST /admin/ingest

        Args:
            file_path: Local file path
            admin_id: Optional (usually taken from JWT on backend)

        Returns:
            Ingest result dict
        """

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        files = {
            "file": (path.name, open(path, "rb"))
        }

        data = {}
        if admin_id:
            data["admin_id"] = admin_id

        response = self.client.post(
            "/admin/ingest",
            files=files,
            data=data
        )

        return self._handle_response(response)

    # ============================================================
    # INTERNAL
    # ============================================================

    def _handle_response(self, response):
        """
        Unified response handler.
        """
        try:
            data = response.json()
        except Exception:
            raise ReckomateAPIError(
                status_code=response.status_code,
                message="Invalid JSON response from server"
            )

        if response.status_code >= 400:
            raise ReckomateAPIError(
                status_code=response.status_code,
                message=data.get("detail") or data.get("message") or "API Error",
                payload=data
            )

        return data
