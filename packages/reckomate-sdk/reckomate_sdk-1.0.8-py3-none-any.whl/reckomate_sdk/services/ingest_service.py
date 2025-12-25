from typing import Dict, Any, Optional


class IngestService:
    """
    SDK proxy for ingestion APIs.
    No file parsing, no DB, no AI.
    """

    def __init__(self, sdk):
        self.sdk = sdk

    # -----------------------------
    # FILE INGEST
    # -----------------------------
    def process_file(
        self,
        owner_id: str,
        owner_field: str = "admin_id",
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "owner_id": owner_id,
            "owner_field": owner_field,
            "file_name": file_name
        }
        return self.sdk.post("/ingest/file", json=payload)

    # -----------------------------
    # TEXT INGEST
    # -----------------------------
    def process_text(
        self,
        text: str,
        owner_id: str,
        owner_field: str = "admin_id",
        source_name: str = "text_input"
    ) -> Dict[str, Any]:
        payload = {
            "text": text,
            "owner_id": owner_id,
            "owner_field": owner_field,
            "source_name": source_name
        }
        return self.sdk.post("/ingest/text", json=payload)

    # -----------------------------
    # AUDIO INGEST
    # -----------------------------
    def process_audio(
        self,
        owner_id: str,
        owner_field: str = "admin_id"
    ) -> Dict[str, Any]:
        payload = {
            "owner_id": owner_id,
            "owner_field": owner_field
        }
        return self.sdk.post("/ingest/audio", json=payload)

    # -----------------------------
    # LIST FILES
    # -----------------------------
    def list_files(
        self,
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {}
        if owner_id:
            params["owner_id"] = owner_id
        return self.sdk.get("/ingest/files", params=params)

    # -----------------------------
    # DELETE FILE
    # -----------------------------
    def delete_file(
        self,
        file_id: str
    ) -> Dict[str, Any]:
        return self.sdk.delete(f"/ingest/file/{file_id}")
