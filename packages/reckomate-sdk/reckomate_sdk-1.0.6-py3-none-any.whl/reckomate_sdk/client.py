# reckomate_sdk/client.py

import httpx
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .exceptions import APIError
from .services.proxy_services import (
    UserService, AdminService, MCQService, RAGService,
    ChatService, AudioQuizService, VideoInterviewService,
    QdrantService, IngestService, ScanService, TokenService
)

logger = logging.getLogger(__name__)


@dataclass
class ServiceRegistry:
    user: UserService
    admin: AdminService
    mcq: MCQService
    rag: RAGService
    chat: ChatService
    audio: AudioQuizService
    video: VideoInterviewService
    qdrant: QdrantService
    ingest: IngestService
    scan: ScanService
    token: TokenService


class ReckomateSDK:
    """
    HTTP-based SDK client for Reckomate backend.
    Proxy-only SDK (NO business logic).
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
        access_token: Optional[str] = None,
    ):
        if not base_url:
            raise ValueError("base_url is required")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            verify=self.verify_ssl,
            headers=self._get_headers(),
        )

        self.services = ServiceRegistry(
            user=UserService(self),
            admin=AdminService(self),
            mcq=MCQService(self),
            rag=RAGService(self),
            chat=ChatService(self),
            audio=AudioQuizService(self),
            video=VideoInterviewService(self),
            qdrant=QdrantService(self),
            ingest=IngestService(self),
            scan=ScanService(self),
            token=TokenService(self),
        )

        logger.info(f"✅ ReckomateSDK connected to {self.base_url}")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "reckomate-sdk/1.0.6",
            "Accept": "application/json",
        }

        token = self.access_token or self.api_key
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        try:
            response = self.client.request(method.upper(), endpoint, **kwargs)
            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            return response.json()

        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            raise APIError(f"{e.response.status_code}: {detail}")

        except httpx.TimeoutException:
            raise APIError(f"Request timed out after {self.timeout}s")

        except Exception as e:
            raise APIError(str(e))

    def get(self, endpoint: str, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs):
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        return self.request("DELETE", endpoint, **kwargs)

    def health_check(self) -> bool:
        try:
            return self.client.get("/health", timeout=5).status_code == 200
        except Exception:
            return False

    def close(self):
        self.client.close()
