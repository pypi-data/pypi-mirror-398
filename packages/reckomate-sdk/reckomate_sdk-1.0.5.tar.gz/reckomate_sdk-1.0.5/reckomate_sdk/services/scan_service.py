# reckomate_sdk/services/scan_service.py

class ScanService:
    def __init__(self, sdk):
        self.sdk = sdk

    def store(self, user_id, scan_text, title, metadata=None):
        return self.sdk.post("/api/scan/store", json={
            "user_id": user_id,
            "scan_text": scan_text,
            "title": title,
            "metadata": metadata
        })

    def get_user_scans(self, user_id):
        return self.sdk.get(f"/api/scan/{user_id}")

    def search(self, user_id, query):
        return self.sdk.get("/api/scan/search", params={
            "user_id": user_id,
            "query": query
        })

    def get_by_id(self, scan_id):
        return self.sdk.get(f"/api/scan/item/{scan_id}")

    def delete(self, scan_id):
        return self.sdk.delete(f"/api/scan/item/{scan_id}")
