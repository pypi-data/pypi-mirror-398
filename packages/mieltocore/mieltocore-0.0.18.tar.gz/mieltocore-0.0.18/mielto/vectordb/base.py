from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mielto.knowledge.document import Document


class VectorDb(ABC):
    """Base class for Vector Databases"""

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def async_create(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def name_exists(self, name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def async_name_exists(self, name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def id_exists(self, id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def content_hash_exists(self, content_hash: str, workspace_id: Optional[str] = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def insert(self, content_hash: str, documents: List[Document], filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def async_insert(
        self, content_hash: str, documents: List[Document], filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> None:
        raise NotImplementedError

    def upsert_available(self) -> bool:
        return False

    @abstractmethod
    def upsert(self, content_hash: str, documents: List[Document], filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def async_upsert(
        self, content_hash: str, documents: List[Document], filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None) -> List[Document]:
        raise NotImplementedError

    @abstractmethod
    async def async_search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> List[Document]:
        raise NotImplementedError

    @abstractmethod
    def drop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def async_drop(self) -> None:
        raise NotImplementedError

    
    @abstractmethod
    def get_chunk(self, vector_id: str, include_embedding: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a chunk by vector ID.
        
        Args:
            vector_id (str): The ID of the vector/chunk to retrieve.
            include_embedding (bool): Whether to include the embedding vector.
            
        Returns:
            Optional[Dict[str, Any]]: Standardized chunk dictionary, or None if not found.
            
        Standard chunk format:
            {
                "id": str,                          # Chunk/vector ID
                "content_id": str,                  # Parent content ID
                "collection_id": str,               # Collection ID
                "workspace_id": str,                # Workspace ID
                "name": Optional[str],              # Chunk name (if available)
                "content": str,                     # Text content of the chunk
                "embedding": Optional[List[float]], # Vector embedding (only if include_embedding=True)
                "metadata": Dict[str, Any],         # Custom metadata
                "created_at": Optional[Any],        # Creation timestamp (if available)
            }
        """
        raise NotImplementedError

    @abstractmethod
    def list_chunks(
        self, 
        content_id: str = None, 
        filters: Optional[Dict[str, Any]] = None, 
        include_embedding: bool = False,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List chunks with metadata using cursor-based pagination.
        
        Args:
            content_id (str, optional): Filter by content ID.
            filters (Dict[str, Any], optional): Additional filters.
                Standard filters: workspace_id, collection_id
                Custom metadata filters are also supported.
            include_embedding (bool): Whether to include embedding vectors.
            limit (int, optional): Maximum number of chunks to return.
            cursor (str, optional): Pagination cursor from previous response.
                For PgVector: Last chunk's ID
                For Qdrant: Last point's ID
                For first page: None
            
        Returns:
            Dict[str, Any]: Dictionary containing:
                - chunks: List[Dict[str, Any]] - List of standardized chunk dictionaries
                - next_cursor: Optional[str] - Cursor for next page (None if no more pages)
                - has_more: bool - Whether there are more chunks available
            
        Standard chunk format:
            {
                "id": str,
                "content_id": str,
                "collection_id": str,
                "workspace_id": str,
                "name": Optional[str],
                "content": str,
                "embedding": Optional[List[float]],
                "metadata": Dict[str, Any],
                "created_at": Optional[Any],
            }
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def async_exists(self) -> bool:
        raise NotImplementedError

    def optimize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_by_collection_id(self, collection_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_by_workspace_id(self, workspace_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_by_name(self, name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_by_metadata(self, metadata: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def update_metadata(self, content_id: str, metadata: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_by_content_id(self, content_id: str) -> bool:
        raise NotImplementedError
