import json
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from models import ShareInfo

# File to store shares data
SHARES_FILE = Path(__file__).parent / "shares.json"


def generate_share_id() -> str:
    """Generate a unique 7-character alphanumeric share ID."""
    # Use lowercase letters and digits
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(7))


def load_shares() -> Dict[str, ShareInfo]:
    """Load shares from JSON file."""
    if not SHARES_FILE.exists():
        return {}
    
    try:
        with open(SHARES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert dict to ShareInfo objects
            shares = {}
            for share_id, share_data in data.items():
                shares[share_id] = ShareInfo(**share_data)
            return shares
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # If file is corrupted, return empty dict
        print(f"Error loading shares: {e}")
        return {}


def save_shares(shares: Dict[str, ShareInfo]) -> None:
    """Save shares to JSON file."""
    # Convert ShareInfo objects to dicts
    data = {}
    for share_id, share_info in shares.items():
        data[share_id] = share_info.model_dump() if hasattr(share_info, 'model_dump') else share_info.dict()
    
    # Write to file atomically
    temp_file = SHARES_FILE.with_suffix('.json.tmp')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    temp_file.replace(SHARES_FILE)


def create_share(
    path: str,
    storage_type: str,
    username: Optional[str],
    permissions: str = 'read',
    expires_at: Optional[int] = None
) -> ShareInfo:
    """Create a new share and return the share info."""
    shares = load_shares()
    
    # Generate unique share ID
    while True:
        share_id = generate_share_id()
        if share_id not in shares:
            break
    
    # Create share info
    share_info = ShareInfo(
        share_id=share_id,
        path=path,
        storage_type=storage_type,
        username=username,
        permissions=permissions,
        expires_at=expires_at,
        created_at=int(datetime.now().timestamp())
    )
    
    # Save to file
    shares[share_id] = share_info
    save_shares(shares)
    
    return share_info


def get_share(share_id: str) -> Optional[ShareInfo]:
    """Get share info by ID. Returns None if share doesn't exist or is expired."""
    shares = load_shares()
    
    if share_id not in shares:
        return None
    
    share = shares[share_id]
    
    # Check if share is expired
    if share.expires_at is not None:
        current_time = int(datetime.now().timestamp())
        if current_time > share.expires_at:
            # Share expired, remove it
            del shares[share_id]
            save_shares(shares)
            return None
    
    return share


def delete_share(share_id: str, username: str) -> bool:
    """Delete a share. Returns True if deleted, False if not found or not owner."""
    shares = load_shares()
    
    if share_id not in shares:
        return False
    
    share = shares[share_id]
    
    # Check if user owns this share (must be the owner of the private storage, or shared)
    if share.storage_type == 'private':
        if share.username != username:
            return False
    # For shared storage, check if user has write permission
    # We'll check this in the API endpoint
    
    del shares[share_id]
    save_shares(shares)
    return True


def list_user_shares(username: str, storage_type: str, path: Optional[str] = None) -> list[ShareInfo]:
    """List shares created by a user for a specific path or storage type."""
    shares = load_shares()
    current_time = int(datetime.now().timestamp())
    
    result = []
    for share in shares.values():
        # Filter expired shares
        if share.expires_at is not None and current_time > share.expires_at:
            continue
        
        # Filter by storage type and username
        if share.storage_type != storage_type:
            continue
        
        if storage_type == 'private' and share.username != username:
            continue
        
        # Filter by path if specified
        if path is not None and share.path != path:
            continue
        
        result.append(share)
    
    return result