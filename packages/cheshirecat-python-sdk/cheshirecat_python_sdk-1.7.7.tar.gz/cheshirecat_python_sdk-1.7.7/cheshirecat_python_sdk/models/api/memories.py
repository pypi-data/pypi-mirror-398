from typing import Dict, List, Any
from pydantic import BaseModel

from cheshirecat_python_sdk.models.api.nested.memories import (
    CollectionsItem,
    MemoryPointsDeleteByMetadataInfo,
    Record,
    MemoryRecallQuery,
    MemoryRecallVectors,
)
from cheshirecat_python_sdk.models.dtos import MemoryPoint


class CollectionPointsDestroyOutput(BaseModel):
    deleted: Dict[str, bool]


class CollectionsOutput(BaseModel):
    collections: List[CollectionsItem]


class MemoryPointDeleteOutput(BaseModel):
    deleted: str


class MemoryPointOutput(MemoryPoint):
    id: str
    vector: List[float] | List[List[float]] | Dict[str, Any]


class MemoryPointsDeleteByMetadataOutput(BaseModel):
    deleted: MemoryPointsDeleteByMetadataInfo


class MemoryPointsOutput(BaseModel):
    points: List[Record]
    next_offset: str | int | None = None


class MemoryRecallOutput(BaseModel):
    query: MemoryRecallQuery
    vectors: MemoryRecallVectors
