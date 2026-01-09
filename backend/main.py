import logging
import zipfile
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles

import fs
from auth import authenticate_user, create_access_token, get_current_user
from models import (
    DirectoryEntry,
    HierarchyEntry,
    LoginRequest,
    LoginResponse,
    MkdirPayload,
    MovePayload,
    CopyPayload,
    DownloadPayload,
    OperationResult,
    CreateFilePayload,
    SaveFilePayload,
)
from security import (
    ROOT_DIR,
    SHARED_DIR,
    USERS_DIR,
    resolve_path,
    check_shared_write_permission,
)

logger = logging.getLogger("backend")

app = FastAPI(title="LAN File Server", docs_url=None, redoc_url=None)

# Ensure the root and storage directories exist at startup
ROOT_DIR.mkdir(parents=True, exist_ok=True)
SHARED_DIR.mkdir(parents=True, exist_ok=True)
USERS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize user folders automatically if they don't exist
from auth import USERS

WELCOME_MESSAGE = """Welcome to your private storage!

This is your personal folder where you can store your files.
Only you have access to this folder.

You can:
- Upload files and folders
- Create new files and directories
- Organize your files however you like

Enjoy using Sarussi's Vault!
"""

def initialize_user_folders():
    """Initialize user folders with welcome files if they don't exist."""
    for username in USERS.keys():
        user_dir = USERS_DIR / username
        welcome_file = user_dir / "welcome.txt"
        
        # Create user directory if it doesn't exist
        if not user_dir.exists():
            user_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder for {username}")
        
        # Create welcome file if it doesn't exist
        if not welcome_file.exists():
            welcome_file.write_text(WELCOME_MESSAGE, encoding="utf-8")
            logger.info(f"Created welcome.txt for {username}")

# Initialize user folders on startup
initialize_user_folders()

STATIC_DIR = Path(__file__).parent / "static"
DEV_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}

# Allow local dev frontend (Vite) to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(DEV_ORIGINS),
    allow_credentials=True,  # Enable credentials for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Dependency to get current user from token
async def get_current_user_from_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Extract and validate JWT token from Authorization header or cookies."""
    token = None
    
    # Try to get token from Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Try to get token from cookies
        token = request.cookies.get("jwt_token")
    
    return get_current_user(token)


# Login endpoint (public, no authentication required)
@app.post("/api/login", response_model=LoginResponse)
def login(login_data: LoginRequest):
    """Authenticate user and return JWT token."""
    if not authenticate_user(login_data.username, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(login_data.username)
    
    # Create response with token
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    
    # Set token in cookie (never expires - set to 10 years)
    # httponly=False so JavaScript can read it for authentication checks
    response.set_cookie(
        key="jwt_token",
        value=access_token,
        httponly=False,  # Allow JavaScript to read for frontend auth checks
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/",  # Make cookie available for entire site
        max_age=10 * 365 * 24 * 60 * 60,  # 10 years (effectively never expires)
    )
    return response


# Verify token endpoint (lightweight check)
@app.get("/api/verify")
def verify_token(current_user: str = Depends(get_current_user_from_token)):
    """Verify that the current token is valid."""
    return {"authenticated": True, "username": current_user}


@app.get("/api/list", response_model=List[DirectoryEntry])
def list_directory(
    path: str = "",
    current_user: str = Depends(get_current_user_from_token),
):
    directory = resolve_path(path, current_user)
    return fs.list_directory(directory)


@app.get("/api/hierarchy", response_model=List[HierarchyEntry])
def get_hierarchy(
    path: str = "",
    current_user: str = Depends(get_current_user_from_token),
):
    """
    Get the full directory hierarchy starting from the given path.
    Returns a recursive structure with all subdirectories and files.
    """
    directory = resolve_path(path, current_user)
    return fs.build_hierarchy(directory)


@app.get("/api/search", response_model=List[HierarchyEntry])
def search_files(
    path: str = "",
    query: str = "",
    current_user: str = Depends(get_current_user_from_token),
):
    """
    Search for files and folders matching the query within the given path.
    Searches recursively in all subdirectories.
    """
    if not query or not query.strip():
        return []
    
    directory = resolve_path(path, current_user)
    return fs.search_files(directory, query.strip())


@app.get("/api/file")
def get_file(
    path: str,
    current_user: str = Depends(get_current_user_from_token),
):
    file_path = resolve_path(path, current_user)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(file_path, filename=file_path.name)


@app.put("/api/file", response_model=OperationResult)
def save_file(
    payload: SaveFilePayload,
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if payload.path == "shared" or payload.path.startswith("shared/") or (payload.path != "private" and not payload.path.startswith("private/") and payload.path == ""):
        check_shared_write_permission(current_user)
    
    file_path = resolve_path(payload.path, current_user)
    
    # Ensure the file exists (or create it)
    if not file_path.exists():
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure it's a file, not a directory
    if file_path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is a directory, not a file")
    
    # Write content to file
    try:
        file_path.write_text(payload.content, encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to save file {file_path}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save file: {str(e)}")
    
    return OperationResult(detail="File saved successfully")


@app.post("/api/upload", response_model=OperationResult)
async def upload_file(
    path: str = "",
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if path == "shared" or path.startswith("shared/") or (path != "private" and not path.startswith("private/") and path == ""):
        check_shared_write_permission(current_user)
    
    target_dir = resolve_path(path, current_user)
    fs.ensure_directory(target_dir)

    original_name = file.filename or ""
    if "/" in original_name or "\\" in original_name or original_name.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    safe_name = Path(original_name).name
    destination = (target_dir / safe_name).resolve()

    # Ensure destination stays inside ROOT_DIR (handles odd filename edge cases)
    if destination != ROOT_DIR and ROOT_DIR not in destination.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid destination")

    fs.ensure_not_exists(destination)
    await fs.save_upload_file(destination, file)
    return OperationResult(detail="File uploaded")


@app.post("/api/upload-multiple", response_model=OperationResult)
async def upload_multiple_files(
    path: str = "",
    files: List[UploadFile] = File(...),
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if path == "shared" or path.startswith("shared/") or (path != "private" and not path.startswith("private/") and path == ""):
        check_shared_write_permission(current_user)
    
    target_dir = resolve_path(path, current_user)
    fs.ensure_directory(target_dir)

    uploaded_count = 0
    for file in files:
        original_name = file.filename or ""
        if original_name.strip() == "":
            continue

        # Handle relative paths from folder uploads (e.g., "folder/subfolder/file.txt")
        # Normalize path separators
        relative_path = original_name.replace("\\", "/")
        path_parts = [p for p in relative_path.split("/") if p and p != "." and p != ".."]
        
        if not path_parts:
            continue

        # Build destination path preserving directory structure
        destination = target_dir
        for part in path_parts:
            destination = destination / part

        destination = destination.resolve()

        # Ensure destination stays inside ROOT_DIR
        if destination != ROOT_DIR and ROOT_DIR not in destination.parents:
            continue

        try:
            # Ensure parent directories exist
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Only create file if it doesn't exist (skip directories)
            if not destination.exists():
                if len(path_parts) > 1 or not file.filename.endswith("/"):
                    # It's a file, not a directory marker
                    fs.ensure_not_exists(destination)
                    await fs.save_upload_file(destination, file)
                    uploaded_count += 1
        except Exception:
            # Skip files that can't be uploaded
            continue

    return OperationResult(detail=f"{uploaded_count} file(s) uploaded")


@app.post("/api/mkdir", response_model=OperationResult)
def make_directory(
    payload: MkdirPayload,
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if payload.path == "shared" or payload.path.startswith("shared/") or (payload.path != "private" and not payload.path.startswith("private/") and payload.path == ""):
        check_shared_write_permission(current_user)
    
    parent = resolve_path(payload.path, current_user)
    fs.ensure_directory(parent)

    name = payload.name.strip()
    name_path = Path(name)
    if name == "" or name_path.is_absolute() or ".." in name_path.parts or name_path.name != name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid directory name")

    target = (parent / name_path).resolve()
    if target != ROOT_DIR and ROOT_DIR not in target.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid destination")

    fs.ensure_not_exists(target)
    target.mkdir(parents=False, exist_ok=False)
    return OperationResult(detail="Directory created")


@app.post("/api/create-file", response_model=OperationResult)
def create_file(
    payload: CreateFilePayload,
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if payload.path == "shared" or payload.path.startswith("shared/") or (payload.path != "private" and not payload.path.startswith("private/") and payload.path == ""):
        check_shared_write_permission(current_user)
    
    parent = resolve_path(payload.path, current_user)
    fs.ensure_directory(parent)

    name = payload.name.strip()
    name_path = Path(name)
    if name == "" or name_path.is_absolute() or ".." in name_path.parts or name_path.name != name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    target = (parent / name_path).resolve()
    if target != ROOT_DIR and ROOT_DIR not in target.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid destination")

    fs.ensure_not_exists(target)
    target.touch(exist_ok=False)
    return OperationResult(detail="File created")


@app.delete("/api/delete", response_model=OperationResult)
def delete_path(
    path: str,
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to delete from shared folder
    if path == "shared" or path.startswith("shared/") or (path != "private" and not path.startswith("private/") and path == ""):
        check_shared_write_permission(current_user)
    
    target = resolve_path(path, current_user)
    # Prevent deleting storage root directories
    if target == ROOT_DIR or target == SHARED_DIR or (target.parent == USERS_DIR):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete storage root directory")
    fs.remove_path(target)
    return OperationResult(detail="Deleted")


@app.post("/api/move", response_model=OperationResult)
def move_path(
    payload: MovePayload,
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if payload.dst == "shared" or payload.dst.startswith("shared/") or (payload.dst != "private" and not payload.dst.startswith("private/") and payload.dst == ""):
        check_shared_write_permission(current_user)
    # Also check if moving from shared folder
    if payload.src == "shared" or payload.src.startswith("shared/") or (payload.src != "private" and not payload.src.startswith("private/") and payload.src == ""):
        check_shared_write_permission(current_user)
    
    src = resolve_path(payload.src, current_user)
    dst = resolve_path(payload.dst, current_user)

    if src == ROOT_DIR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move root directory")

    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    if not dst.parent.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination parent not found")
    if not dst.parent.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Destination parent is not a directory")

    fs.ensure_not_exists(dst)
    fs.move_path(src, dst)
    return OperationResult(detail="Moved")


@app.post("/api/copy", response_model=OperationResult)
def copy_path(
    payload: CopyPayload,
    current_user: str = Depends(get_current_user_from_token),
):
    # Check if trying to write to shared folder
    if payload.dst == "shared" or payload.dst.startswith("shared/") or (payload.dst != "private" and not payload.dst.startswith("private/") and payload.dst == ""):
        check_shared_write_permission(current_user)
    # Also check if copying from shared folder (for consistency, though copy doesn't modify source)
    if payload.src == "shared" or payload.src.startswith("shared/") or (payload.src != "private" and not payload.src.startswith("private/") and payload.src == ""):
        check_shared_write_permission(current_user)
    
    src = resolve_path(payload.src, current_user)
    dst = resolve_path(payload.dst, current_user)

    if src == ROOT_DIR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot copy root directory")

    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    if not dst.parent.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination parent not found")
    if not dst.parent.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Destination parent is not a directory")

    fs.ensure_not_exists(dst)
    fs.copy_path(src, dst)
    return OperationResult(detail="Copied")


def add_to_zip(zip_file: zipfile.ZipFile, path: Path, base_path: Path, arcname_prefix: str = ""):
    """Recursively add files and directories to zip file."""
    if path.is_file():
        arcname = f"{arcname_prefix}/{path.name}" if arcname_prefix else path.name
        zip_file.write(path, arcname)
    elif path.is_dir():
        # Add all items in the directory
        for item in path.iterdir():
            item_arcname = f"{arcname_prefix}/{item.name}" if arcname_prefix else item.name
            add_to_zip(zip_file, item, base_path, item_arcname)


@app.post("/api/download-zip")
def download_as_zip(
    payload: DownloadPayload,
    current_user: str = Depends(get_current_user_from_token),
):
    """Download multiple files/folders as a zip archive."""
    if not payload.paths:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No paths provided")
    
    # Create a temporary zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_zip_path = Path(temp_zip.name)
    temp_zip.close()
    
    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for path_str in payload.paths:
                resolved_path = resolve_path(path_str, current_user)
                if not resolved_path.exists():
                    continue
                
                # Get the base name for the archive
                if resolved_path.is_file():
                    zip_file.write(resolved_path, resolved_path.name)
                elif resolved_path.is_dir():
                    # Add directory and all its contents
                    add_to_zip(zip_file, resolved_path, resolved_path, resolved_path.name)
        
        # Determine zip filename
        if len(payload.paths) == 1:
            # Single item - use its name
            single_path = resolve_path(payload.paths[0], current_user)
            zip_filename = f"{single_path.name}.zip"
        else:
            # Multiple items - use a generic name
            zip_filename = "download.zip"
        
        # Use StreamingResponse to allow cleanup after download
        def generate():
            with open(temp_zip_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk
            # Clean up after streaming
            if temp_zip_path.exists():
                temp_zip_path.unlink()
        
        return StreamingResponse(
            generate(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
    except Exception as e:
        # Clean up temp file on error
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# SPA routing catch-all - serve index.html for all non-API routes
# This must be registered AFTER all API routes but handles routes like /shared, /private, etc.
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve static files or index.html for SPA routing.
    This ensures that routes like /shared, /private, etc. work on page reload.
    """
    # Don't interfere with API routes (they're registered before this)
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Try to serve the requested file if it exists (for assets, favicon, etc.)
    static_file_path = STATIC_DIR / full_path
    if static_file_path.exists() and static_file_path.is_file():
        return FileResponse(static_file_path)
    
    # For all other routes (like /shared, /private, /shared/folder, etc.), serve index.html
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Not Found")

# Note: We're not using app.mount for static files anymore since we handle it manually above
# This gives us better control over SPA routing
