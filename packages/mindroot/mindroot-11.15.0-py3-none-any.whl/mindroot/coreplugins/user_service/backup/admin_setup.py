import os
import random
import string
from datetime import datetime
import bcrypt
from typing import Tuple, Optional
from pathlib import Path
import json

from .models import UserAuth, UserBase

def generate_random_credentials(prefix: str = \"admin\", length: int = 8) -> Tuple[str, str]:
    """Generate random admin username and password."""
    chars = string.ascii_letters + string.digits
    random_suffix = ''.join(random.choices(chars, k=length))
    random_pass = ''.join(random.choices(chars + \"!@#$%^&*\", k=16))
    
    return f\"{prefix}{random_suffix}\", random_pass

def get_admin_credentials(user_data_root: str = \"data/users\") -> Tuple[Optional[str], Optional[str]]:
    """
    Get admin credentials from environment variables or generate new ones if user database is empty.
    Returns tuple of (username, password) or (None, None) if admin setup not needed.
    """
    # Check environment variables first
    env_user = os.environ.get('ADMIN_USER')
    env_pass = os.environ.get('ADMIN_PASS')
    if env_user and env_pass:
        return env_user, env_pass
        
    # Check if users directory exists and has any files
    user_dir = Path(user_data_root)
    if user_dir.exists() and any(user_dir.glob('*/auth.json')):
        return None, None  # Users exist, no need for initial admin
        
    # Generate random credentials
    username, password = generate_random_credentials()
    print("\n" + "="*50)
    print("INITIAL ADMIN CREDENTIALS GENERATED:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("="*50 + "\n")
    
    return username, password

def create_admin_user(username: str, password: str, user_data_root: str = \"data/users\") -> Optional[UserBase]:
    """
    Create the admin user if it doesn't exist.
    Returns UserBase instance if created, None if user already exists.
    """
    user_dir = Path(user_data_root) / username
    auth_file = user_dir / "auth.json"
    
    if auth_file.exists():
        return None
        
    # Create user directory
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Create auth data
    now = datetime.utcnow().isoformat()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    auth_data = UserAuth(
        username=username,
        email="",  # Optional: could be set via env var
        password_hash=password_hash,
        created_at=now,
        last_login=None,
        email_verified=True,  # Admin user is pre-verified
        verification_token=None,
        verification_expires=None,
        role="admin"  # Add this to UserAuth model
    )
    
    # Save auth data
    with open(auth_file, 'w') as f:
        json.dump(auth_data.dict(), f, indent=2, default=str)
        
    # Initialize empty settings and workspace
    with open(user_dir / "settings.json", 'w') as f:
        json.dump({}, f)
    with open(user_dir / "workspace.json", 'w') as f:
        json.dump({}, f)
    
    return UserBase(**auth_data.dict())
