from typing import Dict, Any, Optional


class ChatService:
    """
    SDK proxy for Chat APIs.
    Mirrors Node proxy behavior exactly.
    """

    def __init__(self, sdk):
        self.sdk = sdk

    # -----------------------------
    # SAVE MESSAGE
    # -----------------------------
    def save(
        self,
        user_id: str,
        role: str,
        message: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "role": role,
            "message": message,
            "document_id": document_id
        }
        return self.sdk.post("/chat/save", json=payload)

    # -----------------------------
    # USER CHAT HISTORY
    # -----------------------------
    def get_history(
        self,
        user_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        params = {
            "limit": limit,
            "offset": offset
        }
        return self.sdk.get(f"/chat/history/{user_id}", params=params)

    # -----------------------------
    # ADMIN – ALL CHAT HISTORY
    # -----------------------------
    def get_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        params = {
            "limit": limit,
            "offset": offset
        }
        return self.sdk.get("/chat/all", params=params)

    # -----------------------------
    # CLEAR USER CHAT
    # -----------------------------
    def clear(self, user_id: str) -> Dict[str, Any]:
        return self.sdk.delete(f"/chat/clear/{user_id}")

    # -----------------------------
    # SEARCH CHAT
    # -----------------------------
    def search(
        self,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        role: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        params = {
            "user_id": user_id,
            "query": query,
            "role": role,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
        return self.sdk.get("/chat/search", params=params)
