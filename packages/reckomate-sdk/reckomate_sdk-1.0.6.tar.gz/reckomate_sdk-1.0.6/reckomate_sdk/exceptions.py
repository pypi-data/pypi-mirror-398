# reckomate_sdk/exceptions.py

class SDKError(Exception):
    """Base exception for all SDK errors"""
    pass


class APIError(SDKError):
    """Raised when an HTTP/API request fails"""
    pass


class ValidationError(SDKError):
    """Raised when input validation fails"""
    pass


class AuthenticationError(SDKError):
    """Raised when authentication fails"""
    pass


class ConfigurationError(SDKError):
    """Raised when SDK configuration is invalid"""
    pass


class ServiceError(SDKError):
    """Raised when a service operation fails"""
    pass


class NotFoundError(SDKError):
    """Raised when a resource is not found"""
    pass


class ProcessingError(SDKError):
    """Raised when document processing fails"""
    pass


class QdrantError(SDKError):
    """Raised when Qdrant operations fail"""
    pass


class OpenAIError(SDKError):
    """Raised when OpenAI operations fail"""
    pass


class DatabaseError(SDKError):
    """Raised when database operations fail"""
    pass
