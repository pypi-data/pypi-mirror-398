# reckomate_sdk/services/video_interview_service.py

class VideoInterviewService:
    def __init__(self, sdk):
        self.sdk = sdk

    def start(self, user_id, file_id, **kwargs):
        return self.sdk.post("/api/video-interview/start", json={
            "user_id": user_id,
            "file_id": file_id,
            **kwargs
        })

    def submit_response(self, interview_id, question_id, **kwargs):
        return self.sdk.post("/api/video-interview/response", json={
            "interview_id": interview_id,
            "question_id": question_id,
            **kwargs
        })

    def get_status(self, interview_id):
        return self.sdk.get(f"/api/video-interview/{interview_id}/status")

    def end(self, interview_id):
        return self.sdk.post(f"/api/video-interview/{interview_id}/end")
