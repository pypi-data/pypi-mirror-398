from pathlib import Path
from typing import Dict, Optional

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class UsersIngestService:
    """
    Users Ingest SDK Service

    Handles:
    - User document / audio / video ingest
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ============================================================
    # INGEST
    # ============================================================

    def ingest_file(
        self,
        file_path: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Upload & ingest a file for a user.

        Backend: POST /users/ingest
        """

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            response = self.client.post(
                "/users/ingest",
                files={"file": (path.name, f)},
                data={"user_id": user_id} if user_id else None
            )

        return self._handle_response(response)

    # ============================================================
    # INTERNAL RESPONSE HANDLER
    # ============================================================

    def _handle_response(self, response):
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
                message=data.get("detail")
                or data.get("message")
                or "Users ingest API error",
                payload=data
            )

        return data
