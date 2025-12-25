from typing import Dict, Any


class AdminService:
    """
    SDK proxy for Admin-related backend APIs.
    This class ONLY forwards HTTP requests to the main backend.
    """

    def __init__(self, sdk):
        self.sdk = sdk

    # -----------------------------
    # AUTH
    # -----------------------------
    def register(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        payload = {
            "email": email,
            "password": password
        }
        return self.sdk.post("/admin/register", json=payload)

    def login(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        payload = {
            "email": email,
            "password": password
        }
        return self.sdk.post("/admin/login", json=payload)

    # -----------------------------
    # ADMIN PROFILE
    # -----------------------------
    def get_by_id(self, admin_id: str) -> Dict[str, Any]:
        return self.sdk.get(f"/admin/{admin_id}")
