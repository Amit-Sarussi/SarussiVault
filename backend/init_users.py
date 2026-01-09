"""
Script to initialize user passwords.
Run this script to set passwords for the 6 users.

Usage:
    python init_users.py

You will be prompted to enter passwords for each user.
"""

from auth import USERS, create_user_password

def main():
    print("Initializing user passwords...")
    print("=" * 50)
    
    for username in USERS.keys():
        while True:
            password = input(f"Enter password for {username}: ")
            if password.strip():
                try:
                    create_user_password(username, password)
                    print(f"✓ Password set for {username}")
                except ValueError as e:
                    print(f"✗ Error: {e}")
                break
            else:
                print("Password cannot be empty. Please try again.")
    
    print("=" * 50)
    print("All user passwords have been initialized!")
    print("\nNote: In production, you should persist these passwords in a database.")
    print("For now, passwords are stored in memory and will be lost on server restart.")

if __name__ == "__main__":
    main()
