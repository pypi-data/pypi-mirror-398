# reckomate_sdk/services/rag_service.py

from typing import Dict, Any, List, Optional
from ..exceptions import APIError


class RAGService:
    """
    SDK proxy for RAG-related backend APIs.
    This class ONLY makes HTTP calls.
    """

    def __init__(self, sdk):
        self.sdk = sdk

    # --------------------------------------------------
    # EASY MODE RAG
    # --------------------------------------------------
    def ask_easy(
        self,
        user_id: str,
        prompt: str,
        file_id: str,
        top_k: int = 15
    ) -> Dict[str, Any]:
        """
        Ask an easy-mode RAG question.
        """
        payload = {
            "user_id": user_id,
            "query": prompt,
            "file_id": file_id,
            "top_k": top_k
        }
        return self.sdk.post("/rag/easy", json=payload)

    # --------------------------------------------------
    # INTELLIGENT MODE RAG
    # --------------------------------------------------
    def ask_intelligent(
        self,
        user_id: str,
        prompt: str,
        file_id: str,
        top_k: int = 20
    ) -> Dict[str, Any]:
        """
        Ask an intelligent-mode RAG question.
        """
        payload = {
            "user_id": user_id,
            "query": prompt,
            "file_id": file_id,
            "top_k": top_k
        }
        return self.sdk.post("/rag/intelligent", json=payload)

    # --------------------------------------------------
    # AUDIO QUIZ
    # --------------------------------------------------
    def generate_audio_quiz(
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

    def evaluate_audio_answer(
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

    # --------------------------------------------------
    # MCQ
    # --------------------------------------------------
    def generate_mcqs(
        self,
        query: str,
        admin_id: str,
        file_id: str,
        top_k: int = 5,
        num_choices: int = 4,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        payload = {
            "query": query,
            "admin_id": admin_id,
            "file_id": file_id,
            "top_k": top_k,
            "num_choices": num_choices,
            "difficulty": difficulty
        }
        return self.sdk.post("/mcq/generate", json=payload)

    def submit_mcq_results(
        self,
        user_id: str,
        mcq_id: str,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "mcq_id": mcq_id,
            "responses": responses
        }
        return self.sdk.post("/mcq/submit", json=payload)

    def get_results_by_user(self, user_id: str) -> Dict[str, Any]:
        return self.sdk.get(f"/mcq/results/{user_id}")
