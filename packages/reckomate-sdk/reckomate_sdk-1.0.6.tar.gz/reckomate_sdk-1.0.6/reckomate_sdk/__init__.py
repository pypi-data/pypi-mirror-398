"""
Reckomate SDK - A Python SDK for Reckomate AI business logic

Provides reusable business logic without HTTP/FastAPI dependencies.

Usage:
    >>> from reckomate_sdk import ReckomateSDK, SDKConfig
    >>> config = SDKConfig(openai_api_key="your-key")
    >>> sdk = ReckomateSDK(config)
    >>> result = sdk.user.register_user("+1234567890", "password")

Version: 1.0.0
Dependencies:
    - OpenAI: 2.8.1
    - Qdrant: 1.16.1
    - MongoDB: 4.15.4
    - Sentence Transformers: 5.1.2
    - LangChain: 1.1.0
    - PyTorch: 2.9.1
"""

__version__ = "1.0.2"
__author__ = "Reckomate AI"
__email__ = "support@reckomate.com"

from .client import ReckomateSDK
from .config.settings import SDKConfig
from .exceptions import (
    SDKError,
    ValidationError,
    AuthenticationError,
    ConfigurationError,
    ServiceError,
    NotFoundError,
    ProcessingError,
    QdrantError,
    OpenAIError,
    DatabaseError,
    FirebaseError,
    ChatError,
    MCQError,
    AudioError,
    VideoError,
    IngestError,
    ScanError
)

# Re-export commonly used schemas
from .schemas.audio_quiz_schema import (
    StartAudioQuizRequest,
    AudioQuizAnswer,
    AudioQuizEvaluation,
    AudioQuizSession
)
from .schemas.mcq_schema import (
    MCQRequest,
    StoreResultBody,
    McqAnswer,
    MCQResponse,
    MCQGenerationResponse
)
from .schemas.video_interview_schema import (
    StartVideoInterviewRequest,
    VideoInterviewQuestion,
    VideoInterviewResponse,
    VideoInterviewEvaluation
)
from .schemas.chat_schema import (
    ChatMessage,
    ChatHistoryResponse,
    SaveMessageRequest
)
from .schemas.rag_schema import (
    AskEasyRequest,
    AskIntelligentRequest,
    AskResponse,
    RAGContextRequest,
    QueryRewriteRequest
)
from .schemas.user_schema import (
    UserRegister,
    UserLogin,
    UserResponse,
    LinkedFile,
    UserLoginResponse
)
from .schemas.admin_schema import (
    AdminRegister,
    AdminLogin,
    AdminResponse
)
from .schemas.upload_schema import (
    UploadResponse,
    ProcessFileRequest,
    ProcessFileResponse
)

# Export models
from .models.user_model import User, UserCreate, UserUpdate, UserResponse
from .models.chat_model import ChatMessage as ChatMessageModel, ChatSession

__all__ = [
    # Main classes
    "ReckomateSDK",
    "SDKConfig",
    
    # Exceptions
    "SDKError",
    "ValidationError",
    "AuthenticationError",
    "ConfigurationError",
    "ServiceError",
    "NotFoundError",
    "ProcessingError",
    "QdrantError",
    "OpenAIError",
    "DatabaseError",
    "FirebaseError",
    "ChatError",
    "MCQError",
    "AudioError",
    "VideoError",
    "IngestError",
    "ScanError",
    
    # Schemas
    "StartAudioQuizRequest",
    "AudioQuizAnswer",
    "AudioQuizEvaluation",
    "AudioQuizSession",
    "MCQRequest",
    "StoreResultBody",
    "McqAnswer",
    "MCQResponse",
    "MCQGenerationResponse",
    "StartVideoInterviewRequest",
    "VideoInterviewQuestion",
    "VideoInterviewResponse",
    "VideoInterviewEvaluation",
    "ChatMessage",
    "ChatHistoryResponse",
    "SaveMessageRequest",
    "AskEasyRequest",
    "AskIntelligentRequest",
    "AskResponse",
    "RAGContextRequest",
    "QueryRewriteRequest",
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "LinkedFile",
    "UserLoginResponse",
    "AdminRegister",
    "AdminLogin",
    "AdminResponse",
    "UploadResponse",
    "ProcessFileRequest",
    "ProcessFileResponse",
    
    # Models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "ChatMessageModel",
    "ChatSession",
]