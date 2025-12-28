"""
Reckomate SDK
~~~~~~~~~~~~~

Python SDK for interacting with Reckomate backend services.
"""

from .client import ReckomateClient
from .services import AdminService, UserService, UsersIngestService, QuestionService


class ReckomateSDK:
    """
    Main SDK entry point.
    """

    def __init__(self, base_url: str, token: str | None = None):
        self._client = ReckomateClient(base_url=base_url, token=token)

        # Service bindings
        self.admin = AdminService(self._client)
        self.users = UserService(self._client)
        self.users_ingest = UsersIngestService(self._client)
        self.questions = QuestionService(self._client)

    def set_token(self, token: str):
        """
        Update auth token dynamically (after login).
        """
        self._client.set_token(token)


__all__ = [
    "ReckomateSDK",
    "ReckomateClient",
    "AdminService",
    "UserService",
    "UsersIngestService",
    "QuestionService",
]
