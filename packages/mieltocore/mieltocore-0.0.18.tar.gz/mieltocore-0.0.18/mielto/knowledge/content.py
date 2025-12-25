from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from mielto.knowledge.reader import Reader
from mielto.knowledge.remote_content.remote_content import RemoteContent
from mielto.utils.common import generate_prefix_ulid
import mimetypes
import sys


class ContentStatus(str, Enum):
    """Enumeration of possible content processing statuses."""

    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileData:
    content: Optional[Union[str, bytes]] = None
    type: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    ext: Optional[str] = None
    mimetype: Optional[str] = None
    uri: Optional[str] = None
    file_id: Optional[str] = None
    path: Optional[str] = None
    protocol: Optional[str] = None
    document_url: Optional[str] = None
    document_type: Optional[str] = "file"
    bucket_name: Optional[str] = None
    object_name: Optional[str] = None
    file_name: Optional[str] = None


    def __post_init__(self):
        if self.content and isinstance(self.content, bytes):
            if self.filename:
                if not self.mimetype:
                    self.mimetype = mimetypes.guess_type(self.filename)[0]
                if not self.ext:
                    self.ext = self.filename.split(".")[-1]
            
        if not self.size:
            self.size = sys.getsizeof(self.content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "type": self.type,
            "filename": self.filename,
            "size": self.size,
            "ext": self.ext,
            "mimetype": self.mimetype,
            "uri": self.uri,
            "file_id": self.file_id,
            "path": self.path,
            "protocol": self.protocol,
            "document_url": self.document_url,
            "document_type": self.document_type,
            "bucket_name": self.bucket_name,
            "object_name": self.object_name,
            "file_name": self.file_name,
        }
            



@dataclass
class ContentAuth:
    password: Optional[str] = None
    credential_id: Optional[str] = None
    connection_id: Optional[str] = None


@dataclass
class Content:
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    auth: Optional[Union[ContentAuth, Dict[str, Any]]] = None
    file_data: Optional[FileData] = None
    metadata: Optional[Dict[str, Any]] = None
    topics: Optional[List[str]] = None
    remote_content: Optional[RemoteContent] = None
    reader: Optional[Reader] = None
    size: Optional[int] = None
    file_type: Optional[str] = None
    content_hash: Optional[str] = None
    status: Optional[ContentStatus] = None
    sync_status: Optional[ContentStatus] = None
    status_message: Optional[str] = None
    workspace_id: Optional[str] = None
    collection_id: Optional[str] = None
    created_at: Optional[int] = None
    definition: Optional[Dict[str, Any]] = None
    updated_at: Optional[int] = None
    external_id: Optional[str] = None
    skip_content_insert: Optional[bool] = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Content":
        return cls(
            id=data.get("id", generate_prefix_ulid("con")),
            name=data.get("name"),
            description=data.get("description"),
            path=data.get("path"),
            url=data.get("url"),
            auth=data.get("auth"),
            file_data=data.get("file_data"),
            metadata=data.get("metadata"),
            topics=data.get("topics"),
            remote_content=data.get("remote_content"),
            reader=data.get("reader"),
            size=data.get("size"),
            file_type=data.get("file_type"),
            content_hash=data.get("content_hash"),
            definition=data.get("definition"),
            status=data.get("status"),
            sync_status=data.get("sync_status"),
            status_message=data.get("status_message"),
            created_at=data.get("created_at"),
            workspace_id=data.get("workspace_id"),
            collection_id=data.get("collection_id"),
            updated_at=data.get("updated_at"),
            external_id=data.get("external_id"),
            skip_content_insert=data.get("skip_content_insert"),
        )
