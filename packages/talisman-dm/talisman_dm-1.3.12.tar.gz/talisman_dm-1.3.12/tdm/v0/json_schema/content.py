from enum import Enum
from typing import Dict, Optional, Tuple

from pydantic import BaseModel, ConfigDict


class NodeType(Enum):
    HEADER = "header"
    TEXT = "text"
    LIST = "list"
    JSON = "json"
    KEY = "key"
    TABLE = "table"
    TABLE_ROW = "row"
    IMAGE = "image"


class NodeMetadata(BaseModel):
    node_type: NodeType
    original_text: Optional[str] = None
    text_translations: Dict[str, str] = {}
    language: Optional[str] = None
    hidden: bool = False
    model_config = ConfigDict(extra='allow')


class NodeMarkup(BaseModel):
    model_config = ConfigDict(extra='allow')


class TreeDocumentContentModel(BaseModel):
    id: str
    metadata: NodeMetadata
    text: str
    nodes: Optional[Tuple['TreeDocumentContentModel', ...]] = None
    markup: NodeMarkup = NodeMarkup()


TreeDocumentContentModel.model_rebuild()
