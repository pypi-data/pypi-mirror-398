"""
Authentication Module

Simple HTTP authentication for OSS version.
Enterprise version can extend this with RBAC/SSO.
"""

import os
import secrets
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Basic HTTP auth
security = HTTPBasic()

# Default credentials (can be overridden via environment)
DEFAULT_USERNAME = os.getenv("BRIEFCASE_USERNAME", "admin")
DEFAULT_PASSWORD = os.getenv("BRIEFCASE_PASSWORD", "changeme")

# Simple user store (in production, this would be a database)
def get_users_db():
    """Get users database with simple password storage for OSS demo."""
    return {
        DEFAULT_USERNAME: {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,  # Plain text for OSS demo
            "disabled": False,
        }
    }

class User:
    """User model for authentication."""

    def __init__(self, username: str, disabled: bool = False):
        self.username = username
        self.disabled = disabled

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    user_data = get_users_db().get(username)
    if not user_data:
        return None
    if password != user_data["password"]:  # Simple comparison for OSS demo
        return None
    if user_data.get("disabled", False):
        return None

    return User(username=user_data["username"], disabled=user_data.get("disabled", False))

async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> User:
    """Get the current authenticated user."""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

# Optional: Add user management functions for enterprise
def create_user(username: str, password: str, disabled: bool = False) -> User:
    """Create a new user (for enterprise extension)."""
    if username in get_users_db():
        raise ValueError(f"User {username} already exists")

    get_users_db()[username] = {
        "username": username,
        "password": password,
        "disabled": disabled,
    }

    return User(username=username, disabled=disabled)

def update_user_password(username: str, new_password: str) -> bool:
    """Update user password."""
    if username not in get_users_db():
        return False

    get_users_db()[username]["password"] = new_password
    return True

def disable_user(username: str) -> bool:
    """Disable a user account."""
    if username not in get_users_db():
        return False

    get_users_db()[username]["disabled"] = True
    return True

def list_users() -> list[str]:
    """List all usernames."""
    return list(get_users_db().keys())