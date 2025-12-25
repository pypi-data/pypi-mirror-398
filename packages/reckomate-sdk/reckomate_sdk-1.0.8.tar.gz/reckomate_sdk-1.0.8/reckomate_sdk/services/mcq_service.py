# reckomate_sdk/services/mcq_service.py

class MCQService:
    def __init__(self, sdk):
        self.sdk = sdk

    def generate(self, query, admin_id, file_id, **kwargs):
        return self.sdk.post("/api/mcqs/generate", json={
            "query": query,
            "admin_id": admin_id,
            "file_id": file_id,
            **kwargs
        })

    def get_all(self):
        return self.sdk.get("/api/mcqs")

    def get_by_id(self, mcq_id):
        return self.sdk.get(f"/api/mcqs/{mcq_id}")

    def store(self, user_id, mcqs):
        return self.sdk.post("/api/mcqs/store", json={
            "user_id": user_id,
            "mcqs": mcqs
        })
