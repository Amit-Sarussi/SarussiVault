from pathlib import Path

from fastapi import HTTPException, status

# Root directory for all filesystem operations
ROOT_DIR = Path("/srv/files").resolve()
SHARED_DIR = ROOT_DIR / "shared"
USERS_DIR = ROOT_DIR / "users"

# Users allowed to write to shared folder
SHARED_WRITE_USERS = {"Aharon", "Amit", "Yuval"}


def _reject(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
    """Raise a sanitized HTTPException with a consistent payload."""
    raise HTTPException(status_code=status_code, detail=detail)


def resolve_path(user_path: str | None, username: str | None = None) -> Path:
    """
    Resolve a user-supplied path that may start with /shared/ or /private/.
    
    Paths starting with /shared/ map to ROOT_DIR/shared/
    Paths starting with /private/ map to ROOT_DIR/users/<username>/
    Other paths are treated as relative to the appropriate storage based on context.
    
    The result is guaranteed to stay within the appropriate directory.
    """
    if user_path is None:
        user_path = ""

    if "\x00" in user_path:
        _reject("Invalid path")

    # Normalize path separators
    user_path = user_path.replace("\\", "/")
    
    # Remove leading slash for processing
    if user_path.startswith("/"):
        user_path = user_path[1:]
    
    # Determine base directory based on path prefix
    if user_path == "shared" or user_path.startswith("shared/"):
        base_dir = SHARED_DIR
        # Remove "shared" or "shared/" prefix
        if user_path == "shared":
            relative_path = ""
        else:
            relative_path = user_path[7:]  # len("shared/") = 7
    elif user_path == "private" or user_path.startswith("private/"):
        if not username:
            _reject("Username required for private storage")
        base_dir = USERS_DIR / username
        # Remove "private" or "private/" prefix
        if user_path == "private":
            relative_path = ""
        else:
            relative_path = user_path[8:]  # len("private/") = 8
            # If path already contains "users/username", remove that prefix too
            # This handles paths from hierarchy API that are relative to ROOT_DIR
            users_prefix = f"users/{username}/"
            if relative_path.startswith(users_prefix):
                relative_path = relative_path[len(users_prefix):]
            elif relative_path == f"users/{username}":
                relative_path = ""
    else:
        # Default to shared if no prefix (for backward compatibility)
        base_dir = SHARED_DIR
        relative_path = user_path

    # Handle empty path (root of storage)
    if not relative_path or relative_path == "":
        return base_dir

    relative = Path(relative_path)

    if relative.is_absolute():
        _reject("Absolute paths are not allowed")

    if any(part == ".." for part in relative.parts):
        _reject("Parent path traversal is not allowed")

    candidate = (base_dir / relative).resolve()

    # Ensure candidate stays within base_dir
    if candidate != base_dir and base_dir not in candidate.parents:
        _reject("Path escapes storage directory")

    return candidate


def check_shared_write_permission(username: str) -> None:
    """Check if user has permission to write to shared folder."""
    if username not in SHARED_WRITE_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to write to shared storage",
        )
