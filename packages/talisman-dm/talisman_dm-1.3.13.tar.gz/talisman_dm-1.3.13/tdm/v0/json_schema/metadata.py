from typing import Any, Dict, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict


class MetadataModel(BaseModel):
    def to_metadata(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class FactMetadataModel(MetadataModel):
    created_time: Optional[int] = None
    modified_time: Optional[int] = None
    fact_confidence: Optional[Tuple[float]] = None
    value_confidence: Union[float, Tuple[float, ...], None] = None  # same as Optional[float, Tuple[float, ...]] (pydantic bug workaround)
    model_config = ConfigDict(extra='allow')


class DocumentMetadataModel(MetadataModel):
    title: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    size: Optional[int] = None
    created_time: Optional[int] = None
    access_time: Optional[int] = None
    modified_time: Optional[int] = None
    publication_date: Optional[int] = None
    publication_author: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    parent_uuid: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    account: Optional[Tuple[str, ...]] = None
    access_level: Optional[str] = None
    user: Optional[str] = None
    path: Optional[str] = None
    trust_level: Optional[float] = None
    markers: Optional[Tuple[str, ...]] = None
    related_concept_id: Optional[str] = None
    preview_text: Optional[str] = None
    story: Optional[str] = None
    model_config = ConfigDict(extra='allow')
