# reckomate_sdk/services/proxy_services.py
"""
Complete proxy services for all backend routes.
Manually created - can be auto-generated from route files.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..exceptions import APIError

logger = logging.getLogger(__name__)


class BaseService:
    """Base service for all proxy services"""
    
    def __init__(self, sdk):
        self.sdk = sdk


# ==================== USER ROUTES ====================
class UserService(BaseService):
    """Proxy to user API endpoints (/api/users/*)"""
    
    # GET /api/users
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.sdk.get("/api/users")
    
    # GET /api/users/{user_id}
    def get_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        return self.sdk.get(f"/api/users/{user_id}")
    
    # POST /api/users/register
    def register(self, phone: str, password: str) -> Dict[str, Any]:
        """Register new user"""
        return self.sdk.post("/api/users/register", json={
            "phone": phone,
            "password": password
        })
    
    # POST /api/users/login
    def login(self, phone: str, password: str, fcm_token: Optional[str] = None) -> Dict[str, Any]:
        """Login user"""
        data = {"phone": phone, "password": password}
        if fcm_token:
            data["fcm_token"] = fcm_token
        return self.sdk.post("/api/users/login", json=data)
    
    # GET /api/users/{user_id}/mcqs
    def get_mcqs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's MCQs"""
        return self.sdk.get(f"/api/users/{user_id}/mcqs")
    
    # GET /api/users/{user_id}/results
    def get_results(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's results"""
        return self.sdk.get(f"/api/users/{user_id}/results")
    
    # POST /api/users/{user_id}/mcqs
    def generate_mcqs(self, user_id: str, query: str, file_id: str, **kwargs) -> Dict[str, Any]:
        """Generate MCQs for user"""
        data = {"query": query, "file_id": file_id, **kwargs}
        return self.sdk.post(f"/api/users/{user_id}/mcqs", json=data)
    
    # POST /api/users/store_results
    def store_results(self, user_id: str, mcq_id: str, responses: List[Dict]) -> Dict[str, Any]:
        """Store MCQ results for user"""
        return self.sdk.post("/api/users/store_results", json={
            "userId": user_id,
            "mcqId": mcq_id,
            "arrayofMcq": responses
        })


# ==================== ADMIN ROUTES ====================
class AdminService(BaseService):
    """Proxy to admin API endpoints (/api/admin/*)"""
    
    # POST /api/admin/register
    def register(self, email: str, password: str) -> Dict[str, Any]:
        """Register admin"""
        return self.sdk.post("/api/admin/register", json={
            "email": email,
            "password": password
        })
    
    # POST /api/admin/login
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login admin"""
        return self.sdk.post("/api/admin/login", json={
            "email": email,
            "password": password
        })
    
    # POST /api/admin/upload
    def upload_file(self, file_content: bytes, filename: str, admin_id: str) -> Dict[str, Any]:
        """Upload file (multipart form)"""
        files = {"file": (filename, file_content)}
        return self.sdk.post("/api/admin/upload", files=files, data={"admin_id": admin_id})
    
    # GET /api/admin/{admin_id}/files
    def get_files(self, admin_id: str) -> List[Dict[str, Any]]:
        """Get admin's files"""
        return self.sdk.get(f"/api/admin/{admin_id}/files")
    
    # POST /api/admin/link-mobile
    def link_mobile(self, admin_id: str, mobile: str, file_id: str) -> Dict[str, Any]:
        """Link mobile to file"""
        return self.sdk.post("/api/admin/link-mobile", json={
            "admin_id": admin_id,
            "mobile": mobile,
            "file_id": file_id
        })


# ==================== MCQ ROUTES ====================
class MCQService(BaseService):
    """Proxy to MCQ API endpoints (/api/mcqs/*)"""
    
    # GET /api/mcqs
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all MCQs"""
        return self.sdk.get("/api/mcqs")
    
    # GET /api/mcqs/{mcq_id}
    def get_by_id(self, mcq_id: str) -> Dict[str, Any]:
        """Get MCQ by ID"""
        return self.sdk.get(f"/api/mcqs/{mcq_id}")
    
    # POST /api/mcqs/generate
    def generate(self, query: str, admin_id: str, file_id: str, **kwargs) -> Dict[str, Any]:
        """Generate MCQs"""
        data = {"query": query, "admin_id": admin_id, "file_id": file_id, **kwargs}
        return self.sdk.post("/api/mcqs/generate", json=data)
    
    # GET /api/mcqs/counts
    def get_counts(self) -> Dict[str, Any]:
        """Get MCQ counts by user"""
        return self.sdk.get("/api/mcqs/counts")
    
    # POST /api/mcqs/store
    def store_generated(self, user_id: str, mcqs: List[Dict], **kwargs) -> Dict[str, Any]:
        """Store generated MCQs"""
        data = {"user_id": user_id, "mcqs": mcqs, **kwargs}
        return self.sdk.post("/api/mcqs/store", json=data)


# ==================== RAG ROUTES ====================
class RAGService(BaseService):
    """Proxy to RAG API endpoints (/api/rag/*)"""
    
    # POST /api/rag/easy
    def ask_easy(self, user_id: str, prompt: str, file_id: str, **kwargs) -> Dict[str, Any]:
        """Ask question (easy mode)"""
        data = {"user_id": user_id, "prompt": prompt, "file_id": file_id, **kwargs}
        return self.sdk.post("/api/rag/easy", json=data)
    
    # POST /api/rag/intelligent
    def ask_intelligent(self, user_id: str, prompt: str, file_id: str, **kwargs) -> Dict[str, Any]:
        """Ask question (intelligent mode)"""
        data = {"user_id": user_id, "prompt": prompt, "file_id": file_id, **kwargs}
        return self.sdk.post("/api/rag/intelligent", json=data)
    
    # GET /api/rag/context
    def get_context(self, user_id: str, file_id: str, **kwargs) -> List[str]:
        """Get context for user/file"""
        params = {"user_id": user_id, "file_id": file_id, **kwargs}
        return self.sdk.get("/api/rag/context", params=params)
    
    # POST /api/rag/rewrite
    def rewrite_query(self, query: str) -> Dict[str, Any]:
        """Rewrite query for better search"""
        return self.sdk.post("/api/rag/rewrite", json={"query": query})


# ==================== CHAT ROUTES ====================
class ChatService(BaseService):
    """Proxy to chat API endpoints (/api/chat/*)"""
    
    # POST /api/chat/messages
    def save_message(self, user_id: str, role: str, message: str, **kwargs) -> Dict[str, Any]:
        """Save chat message"""
        data = {"user_id": user_id, "role": role, "message": message, **kwargs}
        return self.sdk.post("/api/chat/messages", json=data)
    
    # GET /api/chat/{user_id}/history
    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get chat history"""
        return self.sdk.get(f"/api/chat/{user_id}/history")
    
    # GET /api/chat/all
    def get_all_history(self) -> List[Dict[str, Any]]:
        """Get all chat history (admin)"""
        return self.sdk.get("/api/chat/all")
    
    # DELETE /api/chat/{user_id}
    def clear_history(self, user_id: str) -> Dict[str, Any]:
        """Clear chat history"""
        return self.sdk.delete(f"/api/chat/{user_id}")


# ==================== AUDIO QUIZ ROUTES ====================
class AudioQuizService(BaseService):
    """Proxy to audio quiz API endpoints (/api/audio-quiz/*)"""
    
    # POST /api/audio-quiz/start
    def start(self, user_id: str, file_id: str, **kwargs) -> Dict[str, Any]:
        """Start audio quiz"""
        data = {"user_id": user_id, "file_id": file_id, **kwargs}
        return self.sdk.post("/api/audio-quiz/start", json=data)
    
    # POST /api/audio-quiz/answer
    def submit_answer(self, session_id: str, question_id: str, user_answer: str) -> Dict[str, Any]:
        """Submit answer"""
        return self.sdk.post("/api/audio-quiz/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "user_answer": user_answer
        })
    
    # GET /api/audio-quiz/{session_id}/status
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Get quiz status"""
        return self.sdk.get(f"/api/audio-quiz/{session_id}/status")
    
    # POST /api/audio-quiz/{session_id}/end
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End quiz session"""
        return self.sdk.post(f"/api/audio-quiz/{session_id}/end")


# ==================== VIDEO INTERVIEW ROUTES ====================
class VideoInterviewService(BaseService):
    """Proxy to video interview API endpoints (/api/video-interview/*)"""
    
    # POST /api/video-interview/start
    def start(self, user_id: str, file_id: str, **kwargs) -> Dict[str, Any]:
        """Start video interview"""
        data = {"user_id": user_id, "file_id": file_id, **kwargs}
        return self.sdk.post("/api/video-interview/start", json=data)
    
    # POST /api/video-interview/response
    def submit_response(self, interview_id: str, question_id: str, **kwargs) -> Dict[str, Any]:
        """Submit video response"""
        data = {"interview_id": interview_id, "question_id": question_id, **kwargs}
        return self.sdk.post("/api/video-interview/response", json=data)
    
    # GET /api/video-interview/{interview_id}/status
    def get_status(self, interview_id: str) -> Dict[str, Any]:
        """Get interview status"""
        return self.sdk.get(f"/api/video-interview/{interview_id}/status")


# ==================== QDRANT ROUTES ====================
class QdrantService(BaseService):
    """Proxy to Qdrant API endpoints (/api/qdrant/*)"""
    
    # GET /api/qdrant/collections
    def get_collections(self, admin_id: str) -> List[str]:
        """Get admin's collections"""
        return self.sdk.get(f"/api/qdrant/collections", params={"admin_id": admin_id})
    
    # DELETE /api/qdrant/collection
    def delete_collection(self, admin_id: str, collection_name: str) -> Dict[str, Any]:
        """Delete collection"""
        return self.sdk.delete("/api/qdrant/collection", params={
            "admin_id": admin_id,
            "collection_name": collection_name
        })
    
    # DELETE /api/qdrant/all
    def delete_all(self, admin_id: str) -> Dict[str, Any]:
        """Delete all collections"""
        return self.sdk.delete("/api/qdrant/all", params={"admin_id": admin_id})
    
    # GET /api/qdrant/search
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search vectors"""
        params = {"query": query, **kwargs}
        return self.sdk.get("/api/qdrant/search", params=params)


# ==================== UPLOAD/INGEST ROUTES ====================
class IngestService(BaseService):
    """Proxy to upload/ingest API endpoints (/api/upload/*, /api/ingest/*)"""
    
    # POST /api/upload/file
    def upload_file(self, file_content: bytes, filename: str, **kwargs) -> Dict[str, Any]:
        """Upload file"""
        files = {"file": (filename, file_content)}
        return self.sdk.post("/api/upload/file", files=files, data=kwargs)
    
    # POST /api/upload/audio
    def upload_audio(self, file_content: bytes, filename: str, **kwargs) -> Dict[str, Any]:
        """Upload audio file"""
        files = {"file": (filename, file_content)}
        return self.sdk.post("/api/upload/audio", files=files, data=kwargs)
    
    # POST /api/ingest/process
    def process_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Process uploaded file"""
        return self.sdk.post("/api/ingest/process", json={
            "file_path": file_path,
            **kwargs
        })


# ==================== SCAN ROUTES ====================
class ScanService(BaseService):
    """Proxy to scan API endpoints (/api/scan/*)"""
    
    # POST /api/scan/store
    def store_scan(self, user_id: str, scan_text: str, **kwargs) -> Dict[str, Any]:
        """Store user scan"""
        data = {"user_id": user_id, "scan_text": scan_text, **kwargs}
        return self.sdk.post("/api/scan/store", json=data)
    
    # GET /api/scan/{user_id}
    def get_scans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's scans"""
        return self.sdk.get(f"/api/scan/{user_id}")
    
    # GET /api/scan/search
    def search_scans(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search user's scans"""
        return self.sdk.get("/api/scan/search", params={
            "user_id": user_id,
            "query": query
        })


# ==================== TOKEN ROUTES ====================
class TokenService(BaseService):
    """Proxy to token API endpoints (/api/token/*)"""
    
    # POST /api/token/refresh
    def refresh(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        return self.sdk.post("/api/token/refresh", json={
            "refresh_token": refresh_token
        })
    
    # POST /api/token/verify
    def verify(self, token: str) -> Dict[str, Any]:
        """Verify token"""
        return self.sdk.post("/api/token/verify", json={"token": token})
    
    # POST /api/token/revoke
    def revoke(self, token: str) -> Dict[str, Any]:
        """Revoke token"""
        return self.sdk.post("/api/token/revoke", json={"token": token})