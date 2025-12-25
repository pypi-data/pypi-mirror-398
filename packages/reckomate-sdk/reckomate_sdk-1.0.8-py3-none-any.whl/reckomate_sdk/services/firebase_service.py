from typing import Dict, Any, List, Optional


class FirebaseService:
    """
    SDK proxy for Firebase-related backend APIs.
    Mirrors Node proxy behavior exactly.
    """

    def __init__(self, sdk):
        self.sdk = sdk

    # -----------------------------
    # FORCE LOGOUT
    # -----------------------------
    def force_logout(
        self,
        fcm_token: str,
        reason: str = "Logged in from another device"
    ) -> Dict[str, Any]:
        payload = {
            "fcm_token": fcm_token,
            "reason": reason
        }
        return self.sdk.post("/firebase/force-logout", json=payload)

    # -----------------------------
    # SINGLE NOTIFICATION
    # -----------------------------
    def send_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "fcm_token": fcm_token,
            "title": title,
            "body": body,
            "data": data
        }
        return self.sdk.post("/firebase/send", json=payload)

    # -----------------------------
    # MULTICAST
    # -----------------------------
    def send_multicast(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "fcm_tokens": fcm_tokens,
            "title": title,
            "body": body,
            "data": data
        }
        return self.sdk.post("/firebase/send-multicast", json=payload)

    # -----------------------------
    # TOPICS
    # -----------------------------
    def subscribe_topic(
        self,
        fcm_tokens: List[str],
        topic: str
    ) -> Dict[str, Any]:
        payload = {
            "fcm_tokens": fcm_tokens,
            "topic": topic
        }
        return self.sdk.post("/firebase/topic/subscribe", json=payload)

    def unsubscribe_topic(
        self,
        fcm_tokens: List[str],
        topic: str
    ) -> Dict[str, Any]:
        payload = {
            "fcm_tokens": fcm_tokens,
            "topic": topic
        }
        return self.sdk.post("/firebase/topic/unsubscribe", json=payload)

    def send_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "topic": topic,
            "title": title,
            "body": body,
            "data": data
        }
        return self.sdk.post("/firebase/topic/send", json=payload)

    # -----------------------------
    # TOKEN VALIDATION
    # -----------------------------
    def validate_token(self, fcm_token: str) -> Dict[str, Any]:
        return self.sdk.post(
            "/firebase/validate-token",
            json={"fcm_token": fcm_token}
        )
