import os
import shutil
from pathlib import Path
from typing import Iterable, List

from fastapi import HTTPException, UploadFile, status

from models import DirectoryEntry
from security import ROOT_DIR

CHUNK_SIZE = 1024 * 1024  # 1MB


def list_directory(path: Path) -> List[DirectoryEntry]:
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if not path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a directory")

    entries: list[DirectoryEntry] = []
    with os.scandir(path) as it:
        for entry in it:
            try:
                stat_result = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                # Entry vanished between scan and stat; skip it.
                continue
            entries.append(
                DirectoryEntry(
                    name=entry.name,
                    is_dir=entry.is_dir(follow_symlinks=False),
                    size=stat_result.st_size,
                    mtime=int(stat_result.st_mtime),
                )
            )
    return entries


async def save_upload_file(destination: Path, upload: UploadFile) -> None:
    # Prevent overwriting existing files
    try:
        with destination.open("xb") as buffer:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                buffer.write(chunk)
    finally:
        await upload.close()


def ensure_directory(path: Path) -> None:
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if not path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a directory")


def ensure_not_exists(path: Path) -> None:
    if path.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target already exists")


def remove_path(path: Path) -> None:
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def move_path(src: Path, dst: Path) -> None:
    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if dst.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Destination already exists")

    src.rename(dst)
