from pathlib import Path

from fastapi import HTTPException, status

# Root directory for all filesystem operations
ROOT_DIR = Path("/srv/files").resolve()


def _reject(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
    """Raise a sanitized HTTPException with a consistent payload."""
    raise HTTPException(status_code=status_code, detail=detail)


def resolve_path(user_path: str | None) -> Path:
    """
    Resolve a user-supplied relative path against ROOT_DIR.

    The result is guaranteed to stay within ROOT_DIR; attempts to escape
    via absolute paths, parent traversal, or symlinks are rejected.
    """
    if user_path is None:
        user_path = ""

    if "\x00" in user_path:
        _reject("Invalid path")

    relative = Path(user_path)

    if relative.is_absolute():
        _reject("Absolute paths are not allowed")

    if any(part == ".." for part in relative.parts):
        _reject("Parent path traversal is not allowed")

    candidate = (ROOT_DIR / relative).resolve()

    if candidate != ROOT_DIR and ROOT_DIR not in candidate.parents:
        _reject("Path escapes root directory")

    return candidate
