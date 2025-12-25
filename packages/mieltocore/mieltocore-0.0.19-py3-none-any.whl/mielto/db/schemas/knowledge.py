from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, model_validator
from mielto.utils.common import generate_prefix_ulid
from mielto.knowledge.content import FileData


class KnowledgeRow(BaseModel):
    """Knowledge Row that is stored in the database"""

    # id for this knowledge, auto-generated if not provided
    id: Optional[str] = None
    name: str
    description: str
    metadata: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    size: Optional[int] = None
    linked_to: Optional[str] = None
    access_count: Optional[int] = None
    status: Optional[str] = None
    sync_status: Optional[str] = None
    definition: Optional[str] = None
    content_hash: Optional[str] = None
    file_data: Optional[Dict[str, Any]] = None
    status_message: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    external_id: Optional[str] = None
    collection_id: Optional[str] = None
    workspace_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def generate_id(self) -> "KnowledgeRow":
        if self.id is None:

            self.id = generate_prefix_ulid("con")
        return self

    def to_dict(self) -> Dict[str, Any]:
        _dict = self.model_dump(exclude={"updated_at"})

        _dict["updated_at"] = datetime.fromtimestamp(self.updated_at).isoformat() if self.updated_at else None

        return _dict
