from typing import Dict, Any


class AudioQuizService:
    """
    SDK proxy for Audio Quiz APIs.
    This matches the Node proxy behavior exactly.
    """

    def __init__(self, sdk):
        self.sdk = sdk

    # -----------------------------
    # START QUIZ
    # -----------------------------
    def start(
        self,
        user_id: str,
        file_id: str,
        num_questions: int = 5
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "file_id": file_id,
            "num_questions": num_questions
        }
        return self.sdk.post("/audioQuiz/start", json=payload)

    # -----------------------------
    # SUBMIT ANSWER
    # -----------------------------
    def submit_answer(
        self,
        user_id: str,
        file_id: str,
        question: str,
        reference_answer: str,
        user_answer: str
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "file_id": file_id,
            "question": question,
            "reference_answer": reference_answer,
            "user_answer": user_answer
        }
        return self.sdk.post("/audioQuiz/answer", json=payload)

    # -----------------------------
    # SESSION STATUS (OPTIONAL)
    # -----------------------------
    def get_status(self, session_id: str) -> Dict[str, Any]:
        return self.sdk.get(f"/audioQuiz/status/{session_id}")

    # -----------------------------
    # END SESSION (OPTIONAL)
    # -----------------------------
    def end(self, session_id: str) -> Dict[str, Any]:
        return self.sdk.post("/audioQuiz/end", json={"session_id": session_id})
