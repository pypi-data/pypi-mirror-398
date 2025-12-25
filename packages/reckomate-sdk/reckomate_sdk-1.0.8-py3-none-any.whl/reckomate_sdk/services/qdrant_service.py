# reckomate_sdk/services/qdrant_service.py

class QdrantService:
    def __init__(self, sdk):
        self.sdk = sdk

    def get_collections(self, admin_id):
        return self.sdk.get("/api/qdrant/collections", params={
            "admin_id": admin_id
        })

    def delete_collection(self, admin_id, collection_name):
        return self.sdk.delete("/api/qdrant/collection", params={
            "admin_id": admin_id,
            "collection_name": collection_name
        })

    def delete_all(self, admin_id):
        return self.sdk.delete("/api/qdrant/all", params={
            "admin_id": admin_id
        })

    def search(self, query, **kwargs):
        return self.sdk.get("/api/qdrant/search", params={
            "query": query,
            **kwargs
        })
