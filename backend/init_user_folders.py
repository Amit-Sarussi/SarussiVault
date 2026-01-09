"""
Script to initialize user folders with welcome files.
Run this script to create private folders for all users.

Usage:
    python init_user_folders.py
"""

from pathlib import Path
from auth import USERS

# Storage directories
ROOT_DIR = Path("/srv/files").resolve()
USERS_DIR = ROOT_DIR / "users"

WELCOME_MESSAGE = """Welcome to your private storage!

This is your personal folder where you can store your files.
Only you have access to this folder.

You can:
- Upload files and folders
- Create new files and directories
- Organize your files however you like

Enjoy using Sarussi's Vault!
"""


def main():
    print("Initializing user folders...")
    print("=" * 50)
    
    # Ensure users directory exists
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    
    for username in USERS.keys():
        user_dir = USERS_DIR / username
        welcome_file = user_dir / "welcome.txt"
        
        # Create user directory if it doesn't exist
        if not user_dir.exists():
            user_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created folder for {username}")
        else:
            print(f"→ Folder for {username} already exists")
        
        # Create welcome file
        if not welcome_file.exists():
            welcome_file.write_text(WELCOME_MESSAGE, encoding="utf-8")
            print(f"  ✓ Created welcome.txt for {username}")
        else:
            print(f"  → welcome.txt for {username} already exists")
    
    print("=" * 50)
    print("All user folders have been initialized!")
    print(f"\nUser folders are located at: {USERS_DIR}")


if __name__ == "__main__":
    main()
