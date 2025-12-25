# reckomate_sdk/services/user_service.py

class UserService:
    def __init__(self, sdk):
        self.sdk = sdk

    def register(self, phone, password):
        return self.sdk.post("/api/users/register", json={
            "phone": phone,
            "password": password
        })

    def login(self, phone, password, fcm_token=None):
        data = {"phone": phone, "password": password}
        if fcm_token:
            data["fcm_token"] = fcm_token
        return self.sdk.post("/api/users/login", json=data)

    def get_all(self):
        return self.sdk.get("/api/users")

    def get_by_id(self, user_id):
        return self.sdk.get(f"/api/users/{user_id}")

    def get_results(self, user_id):
        return self.sdk.get(f"/api/users/{user_id}/results")

    def get_mcqs(self, user_id):
        return self.sdk.get(f"/api/users/{user_id}/mcqs")

    def store_results(self, user_id, mcq_id, responses):
        return self.sdk.post("/api/users/store_results", json={
            "userId": user_id,
            "mcqId": mcq_id,
            "arrayofMcq": responses
        })
