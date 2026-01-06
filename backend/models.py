from pydantic import BaseModel, Field


class DirectoryEntry(BaseModel):
    name: str
    is_dir: bool
    size: int
    mtime: int = Field(..., description="Last modified time (epoch seconds)")


class PathPayload(BaseModel):
    path: str


class MkdirPayload(BaseModel):
    path: str
    name: str


class MovePayload(BaseModel):
    src: str
    dst: str


class OperationResult(BaseModel):
    success: bool = True
    detail: str | None = None
