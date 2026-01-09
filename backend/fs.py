import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fastapi import HTTPException, UploadFile, status

from models import DirectoryEntry, HierarchyEntry
from security import ROOT_DIR

CHUNK_SIZE = 1024 * 1024  # 1MB
MAX_CHUNK_SIZE = 1024 * 1024  # 1MB (keep under 1.4MB limit)

# Store active chunked uploads: upload_id -> metadata
_chunked_uploads: Dict[str, dict] = {}

# Temporary directory for chunk storage
TEMP_CHUNKS_DIR = Path(tempfile.gettempdir()) / "sarussi_vault_chunks"
TEMP_CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


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


def copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if dst.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Destination already exists")

    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def build_hierarchy(path: Path) -> List[HierarchyEntry]:
    """
    Recursively build the full directory hierarchy starting from the given path.
    
    Args:
        path: The directory path to start from (should be within ROOT_DIR)
    
    Returns:
        List of HierarchyEntry objects representing the full tree structure
    """
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if not path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a directory")
    
    entries: List[HierarchyEntry] = []
    
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    stat_result = entry.stat(follow_symlinks=False)
                    is_dir = entry.is_dir(follow_symlinks=False)
                    
                    # Calculate relative path from ROOT_DIR
                    entry_path = Path(entry.path)
                    if entry_path == ROOT_DIR:
                        rel_path = ""
                    else:
                        rel_path = str(entry_path.relative_to(ROOT_DIR))
                    
                    hierarchy_entry = HierarchyEntry(
                        name=entry.name,
                        path=rel_path,
                        is_dir=is_dir,
                        size=stat_result.st_size,
                        mtime=int(stat_result.st_mtime),
                        children=None
                    )
                    
                    # Recursively load children for directories
                    if is_dir:
                        try:
                            children = build_hierarchy(entry_path)
                            hierarchy_entry.children = children if children else []
                        except (PermissionError, OSError):
                            # If we can't read a subdirectory, just mark it as empty
                            hierarchy_entry.children = []
                    
                    entries.append(hierarchy_entry)
                except (FileNotFoundError, PermissionError, OSError):
                    # Skip entries we can't access
                    continue
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # Sort: folders first, then files; each group alphabetical
    entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
    
    return entries


def init_chunked_upload(
    upload_id: str,
    destination: Path,
    total_size: int,
    total_chunks: int,
) -> None:
    """Initialize a chunked upload session."""
    # Ensure destination parent directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure destination doesn't exist
    ensure_not_exists(destination)
    
    # Store upload metadata
    _chunked_uploads[upload_id] = {
        "destination": destination,
        "total_size": total_size,
        "total_chunks": total_chunks,
        "received_chunks": set(),
        "chunks_dir": TEMP_CHUNKS_DIR / upload_id,
    }
    
    # Create directory for this upload's chunks
    _chunked_uploads[upload_id]["chunks_dir"].mkdir(parents=True, exist_ok=True)


def save_chunk(upload_id: str, chunk_index: int, chunk_data: bytes) -> None:
    """Save a chunk for a chunked upload."""
    if upload_id not in _chunked_uploads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found. It may have expired."
        )
    
    upload_meta = _chunked_uploads[upload_id]
    chunks_dir = upload_meta["chunks_dir"]
    
    # Save chunk to temporary file
    chunk_file = chunks_dir / f"chunk_{chunk_index}"
    with chunk_file.open("xb") as f:
        f.write(chunk_data)
    
    # Track received chunk
    upload_meta["received_chunks"].add(chunk_index)


def finalize_chunked_upload(upload_id: str) -> None:
    """Finalize a chunked upload by assembling all chunks into the final file."""
    if upload_id not in _chunked_uploads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found. It may have expired."
        )
    
    upload_meta = _chunked_uploads[upload_id]
    destination = upload_meta["destination"]
    total_chunks = upload_meta["total_chunks"]
    received_chunks = upload_meta["received_chunks"]
    chunks_dir = upload_meta["chunks_dir"]
    
    # Verify all chunks were received
    if len(received_chunks) != total_chunks:
        missing = set(range(total_chunks)) - received_chunks
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing chunks: {sorted(missing)}"
        )
    
    try:
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Assemble chunks in order
        with destination.open("xb") as output_file:
            for chunk_index in range(total_chunks):
                chunk_file = chunks_dir / f"chunk_{chunk_index}"
                if not chunk_file.exists():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Chunk {chunk_index} not found"
                    )
                
                with chunk_file.open("rb") as chunk_input:
                    shutil.copyfileobj(chunk_input, output_file)
    finally:
        # Clean up chunks directory
        if chunks_dir.exists():
            shutil.rmtree(chunks_dir)
        
        # Remove upload metadata
        del _chunked_uploads[upload_id]


def cleanup_chunked_upload(upload_id: str) -> None:
    """Clean up a chunked upload session (e.g., on error or timeout)."""
    if upload_id in _chunked_uploads:
        upload_meta = _chunked_uploads[upload_id]
        chunks_dir = upload_meta["chunks_dir"]
        
        # Remove chunks directory
        if chunks_dir.exists():
            shutil.rmtree(chunks_dir)
        
        # Remove upload metadata
        del _chunked_uploads[upload_id]


def search_files(path: Path, query: str) -> List[HierarchyEntry]:
    """
    Recursively search for files and folders matching the query within the given path.
    
    Args:
        path: The directory path to search in (should be within ROOT_DIR)
        query: The search query (case-insensitive partial match)
    
    Returns:
        List of HierarchyEntry objects matching the query (with full paths relative to ROOT_DIR)
    """
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if not path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a directory")
    
    query_lower = query.lower()
    results: List[HierarchyEntry] = []
    
    try:
        # Recursively walk through the directory
        for root, dirs, files in os.walk(path):
            root_path = Path(root)
            
            # Search in directory names
            for dir_name in dirs:
                if query_lower in dir_name.lower():
                    dir_path = root_path / dir_name
                    try:
                        stat_result = dir_path.stat(follow_symlinks=False)
                        # Calculate relative path from ROOT_DIR
                        if dir_path == ROOT_DIR:
                            rel_path = ""
                        else:
                            rel_path = str(dir_path.relative_to(ROOT_DIR))
                        
                        results.append(
                            HierarchyEntry(
                                name=dir_name,
                                path=rel_path,
                                is_dir=True,
                                size=stat_result.st_size,
                                mtime=int(stat_result.st_mtime),
                                children=None
                            )
                        )
                    except (FileNotFoundError, PermissionError, OSError):
                        continue
            
            # Search in file names
            for file_name in files:
                if query_lower in file_name.lower():
                    file_path = root_path / file_name
                    try:
                        stat_result = file_path.stat(follow_symlinks=False)
                        # Calculate relative path from ROOT_DIR
                        if file_path == ROOT_DIR:
                            rel_path = ""
                        else:
                            rel_path = str(file_path.relative_to(ROOT_DIR))
                        
                        results.append(
                            HierarchyEntry(
                                name=file_name,
                                path=rel_path,
                                is_dir=False,
                                size=stat_result.st_size,
                                mtime=int(stat_result.st_mtime),
                                children=None
                            )
                        )
                    except (FileNotFoundError, PermissionError, OSError):
                        continue
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # Sort: folders first, then files; each group alphabetical
    results.sort(key=lambda e: (not e.is_dir, e.name.lower()))
    
    return results
