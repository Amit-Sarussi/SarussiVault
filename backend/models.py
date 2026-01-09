from pydantic import BaseModel, Field
from typing import List, Optional


class DirectoryEntry(BaseModel):
    name: str
    is_dir: bool
    size: int
    mtime: int = Field(..., description="Last modified time (epoch seconds)")


class HierarchyEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    mtime: int = Field(..., description="Last modified time (epoch seconds)")
    children: Optional[List['HierarchyEntry']] = None

    class Config:
        # Allow recursive models
        pass


# Update forward references for recursive model (Pydantic v2)
try:
    HierarchyEntry.model_rebuild()
except AttributeError:
    # Pydantic v1 doesn't have model_rebuild, skip it
    pass


class PathPayload(BaseModel):
    path: str


class MkdirPayload(BaseModel):
    path: str
    name: str


class CreateFilePayload(BaseModel):
    path: str
    name: str


class MovePayload(BaseModel):
    src: str
    dst: str


class CopyPayload(BaseModel):
    src: str
    dst: str


class DownloadPayload(BaseModel):
    paths: List[str]


class SaveFilePayload(BaseModel):
    path: str
    content: str


class OperationResult(BaseModel):
    success: bool = True
    detail: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SearchResult(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    mtime: int = Field(..., description="Last modified time (epoch seconds)")
