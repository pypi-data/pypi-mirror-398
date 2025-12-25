from typing import Dict, Optional
from pathlib import Path

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class UserService:
    def __init__(self, client: ReckomateClient):
        self.client = client

    # AUTH
    def login(self, email: str = None, phone: str = None) -> Dict:
        res = self.client.post("/users/login", json={
            "email": email,
            "phone": phone
        })
        return self._handle(res)

    def register(self, email: str = None, phone: str = None) -> Dict:
        res = self.client.post("/users/register", json={
            "email": email,
            "phone": phone
        })
        return self._handle(res)

    def resend_otp(self, email: str = None, phone: str = None) -> Dict:
        res = self.client.post("/users/resend-otp", json={
            "email": email,
            "phone": phone
        })
        return self._handle(res)

    def verify_otp(
        self,
        otp: str,
        email: str = None,
        phone: str = None,
        fcm_token: str | None = None
    ) -> Dict:
        res = self.client.post("/users/verify-otp", json={
            "otp": otp,
            "email": email,
            "phone": phone,
            "fcm_token": fcm_token
        })
        return self._handle(res)

    # PROFILE
    def get_profile(self, user_id: str) -> Dict:
        res = self.client.get(f"/users/{user_id}")
        return self._handle(res)

    def update_profile(
        self,
        user_id: str,
        name: str,
        email: str,
        phone: str,
        profile_image_path: Optional[str] = None
    ) -> Dict:

        data = {
            "name": name,
            "email": email,
            "phone": phone
        }

        files = None
        if profile_image_path:
            p = Path(profile_image_path)
            files = {"profile_image": (p.name, open(p, "rb"))}

        res = self.client.put(
            f"/users/{user_id}",
            data=data,
            files=files
        )
        return self._handle(res)

    def _handle(self, response):
        try:
            data = response.json()
        except Exception:
            raise ReckomateAPIError(response.status_code, "Invalid response")

        if response.status_code >= 400:
            raise ReckomateAPIError(
                response.status_code,
                data.get("message") or data.get("detail") or "User API error",
                data
            )
        return data
