import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import fs
from models import DirectoryEntry, MkdirPayload, MovePayload, OperationResult
from security import ROOT_DIR, resolve_path

logger = logging.getLogger("backend")

app = FastAPI(title="LAN File Server", docs_url=None, redoc_url=None)

# Ensure the root exists at startup
ROOT_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).parent / "static"


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


@app.get("/api/list", response_model=List[DirectoryEntry])
def list_directory(path: str = ""):
    directory = resolve_path(path)
    return fs.list_directory(directory)


@app.get("/api/file")
def get_file(path: str):
    file_path = resolve_path(path)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(file_path, filename=file_path.name)


@app.post("/api/upload", response_model=OperationResult)
async def upload_file(path: str = "", file: UploadFile = File(...)):
    target_dir = resolve_path(path)
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


@app.post("/api/mkdir", response_model=OperationResult)
def make_directory(payload: MkdirPayload):
    parent = resolve_path(payload.path)
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


@app.delete("/api/delete", response_model=OperationResult)
def delete_path(path: str):
    target = resolve_path(path)
    if target == ROOT_DIR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete root directory")
    fs.remove_path(target)
    return OperationResult(detail="Deleted")


@app.post("/api/move", response_model=OperationResult)
def move_path(payload: MovePayload):
    src = resolve_path(payload.src)
    dst = resolve_path(payload.dst)

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


# Mount Vite build output for SPA routing
app.mount(
    "/",
    StaticFiles(directory=STATIC_DIR, html=True),
    name="static",
)
