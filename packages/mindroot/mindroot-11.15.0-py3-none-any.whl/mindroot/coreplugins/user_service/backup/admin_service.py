import os
import random
import string
from typing import Tuple, Optional, Set
from pathlib import Path
import json
from datetime import datetime
from .models import UserAuth, UserCreate, UserBase
from lib.providers.services import service

def generate_random_credentials(prefix: str='admin', length: int=8) -> Tuple[str, str]:
    """Generate random admin username and password."""
    chars = string.ascii_letters + string.digits
    random_suffix = ''.join(random.choices(chars, k=length))
    random_pass = ''.join(random.choices(chars + '!@#$%^&*', k=16))
    return (f'{prefix}{random_suffix}', random_pass)

async def check_for_admin(user_data_root: str) -> bool:
    """Check if any admin user exists."""
    if not os.path.exists(user_data_root):
        return False
    for username in os.listdir(user_data_root):
        auth_file = os.path.join(user_data_root, username, 'auth.json')
        if os.path.exists(auth_file):
            with open(auth_file, 'r') as f:
                try:
                    auth_data = UserAuth(**json.load(f))
                    if 'admin' in auth_data.roles:
                        return True
                except:
                    continue
    return False

@service()
async def initialize_admin(user_data_root: str) -> Tuple[Optional[str], Optional[str]]:
    """Check for and create admin user if needed.
    Returns tuple of (username, password) if created, (None, None) if admin exists.
    """
    if await check_for_admin(user_data_root):
        return (None, None)
    env_user = os.environ.get('ADMIN_USER')
    env_pass = os.environ.get('ADMIN_PASS')
    username = env_user
    password = env_pass
    if not (username and password):
        username, password = generate_random_credentials()
    return (username, password)

@service()
async def has_role(username: str, role: str, user_data_root: str) -> bool:
    """Check if user has specified role"""
    auth_file = os.path.join(user_data_root, username, 'auth.json')
    if not os.path.exists(auth_file):
        return False
    with open(auth_file, 'r') as f:
        try:
            auth_data = UserAuth(**json.load(f))
            return role in auth_data.roles
        except:
            return False

@service()
async def add_role(username: str, role: str, user_data_root: str, context=None) -> bool:
    """Add a role to a user. Requires admin access."""
    if context and (not await has_role(context.username, 'admin', user_data_root)):
        raise PermissionError('Admin access required to modify roles')
    auth_file = os.path.join(user_data_root, username, 'auth.json')
    if not os.path.exists(auth_file):
        return False
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    if role not in auth_data.roles:
        auth_data.roles.add(role)
        with open(auth_file, 'w') as f:
            json.dump(auth_data.dict(), f, indent=2, default=str)
    return True

@service()
async def remove_role(username: str, role: str, user_data_root: str, context=None) -> bool:
    """Remove a role from a user. Requires admin access."""
    if context and (not await has_role(context.username, 'admin', user_data_root)):
        raise PermissionError('Admin access required to modify roles')
    if role == 'user':
        raise ValueError("Cannot remove 'user' role")
    auth_file = os.path.join(user_data_root, username, 'auth.json')
    if not os.path.exists(auth_file):
        return False
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    if role in auth_data.roles:
        auth_data.roles.remove(role)
        with open(auth_file, 'w') as f:
            json.dump(auth_data.dict(), f, indent=2, default=str)
    return True