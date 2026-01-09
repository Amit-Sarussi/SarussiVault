import hashlib
import os
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status

# Load environment variables from .env file
load_dotenv()

# JWT secret key - loaded from .env file or environment variable
# In production, set JWT_SECRET_KEY as an environment variable on your server
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY not found. Please set it in .env file or as an environment variable."
    )
JWT_ALGORITHM = "HS256"

# User database - in production, this should be in a proper database
# Format: username -> hashed_password
USERS = {
    "Amit": "b722a33500f5e30af6d70a0010aff2ee1282b7e25a1616064bd14716e890512e",  # Will be set when password is provided
    "Tal": "995be2de94d944ace0ad0bfeae6dcbb2144b0249cbaf9cf7d257aeebdf662d1f",
    "Yuval": "79aa8c96cf1a98447125559cf1a0e9acbfb7cdd2faf3a5106a57bfd05ea49f8a",
    "Shahar": "3ba478bd3c27da06752c1da484673e673dd849bdb9bb7e339d7423c40d76ff90",
    "Liraz": "9d7b36775f196f5771bd929cbe57335fd72dc403e622d78d4fdcc892713e2439",
    "Aharon": "2438f74ac617a30404f2a5772f7e90eafc7e5cda9a362b0fb16d81c2b337a74a",
}


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 (in production, use bcrypt or argon2)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    return hash_password(password) == hashed


def create_user_password(username: str, password: str) -> None:
    """Set the password for a user (call this to initialize users)."""
    if username not in USERS:
        raise ValueError(f"User {username} does not exist")
    USERS[username] = hash_password(password)


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password."""
    if username not in USERS:
        return False
    if USERS[username] is None:
        return False  # Password not set yet
    return verify_password(password, USERS[username])


def create_access_token(username: str) -> str:
    """Create a JWT token for a user (never expires)."""
    payload = {
        "sub": username,  # Subject (username)
        # No expiration - token never expires
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Decode a JWT token and return the username."""
    try:
        # Use decode with options to skip expiration verification
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}  # Skip expiration check
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(token: Optional[str]) -> str:
    """Get the current user from a JWT token."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return decode_access_token(token)