"""
Admin Configuration Management
Stores and manages admin credentials securely
"""

import json
import hashlib
from pathlib import Path
import os
import logging
from typing import Dict, Optional

# Path to store admin credentials
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "admin_users.json"

def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)
    # Set restrictive permissions (owner read/write only)
    if os.name != 'nt':  # Unix-like systems
        os.chmod(CONFIG_DIR, 0o700)

def load_admin_users() -> Dict[str, str]:
    """
    Load admin users from config file or environment variable.
    Returns dict mapping username to password hash.
    """
    # First, check environment variable (highest priority)
    env_users = os.getenv("ALLOWED_USERS", "")
    if env_users:
        users = {}
        for user_pass in env_users.split(","):
            if ":" in user_pass:
                username, password = user_pass.split(":", 1)
                users[username.strip()] = hashlib.sha256(password.strip().encode()).hexdigest()
        return users
    
    # Second, check config file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logging.error(f"Error loading admin config: {e}")
    
    # Default (development only)
    if os.getenv("NODE_ENV") == "production" or os.getenv("RAILWAY_ENVIRONMENT"):
        logging.warning("SECURITY: Admin users not configured! Please set ALLOWED_USERS environment variable or use admin settings.")
        return {}
    
    # Development default
    default_users = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest()
    }
    save_admin_users(default_users)
    return default_users

def save_admin_users(users: Dict[str, str]) -> bool:
    """
    Save admin users to config file.
    Returns True if successful, False otherwise.
    """
    try:
        ensure_config_dir()
        
        # Backup existing file if it exists
        if CONFIG_FILE.exists():
            backup_file = CONFIG_DIR / f"admin_users.json.backup"
            if backup_file.exists():
                backup_file.unlink()
            CONFIG_FILE.rename(backup_file)
        
        # Write new config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        
        # Set restrictive permissions (owner read/write only)
        if os.name != 'nt':  # Unix-like systems
            os.chmod(CONFIG_FILE, 0o600)
        
        logging.info("Admin users config saved successfully")
        return True
    except Exception as e:
        logging.error(f"Error saving admin config: {e}")
        return False

def update_admin_user(username: str, old_password: str, new_password: Optional[str] = None) -> tuple[bool, str]:
    """
    Update admin user password.
    If new_password is None, just verify the old password (for deletion).
    Returns (success, message)
    """
    users = load_admin_users()
    old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
    
    # Verify old password
    if username not in users or users[username] != old_password_hash:
        return False, "Invalid username or password"
    
    if new_password is None:
        # Delete user
        del users[username]
        message = f"User '{username}' deleted"
    else:
        # Update password
        users[username] = hashlib.sha256(new_password.encode()).hexdigest()
        message = f"Password updated for user '{username}'"
    
    if save_admin_users(users):
        return True, message
    return False, "Failed to save admin configuration"

def add_admin_user(username: str, password: str) -> tuple[bool, str]:
    """
    Add a new admin user.
    Returns (success, message)
    """
    users = load_admin_users()
    
    if username in users:
        return False, f"User '{username}' already exists"
    
    users[username] = hashlib.sha256(password.encode()).hexdigest()
    
    if save_admin_users(users):
        return True, f"User '{username}' added successfully"
    return False, "Failed to save admin configuration"

def get_admin_users() -> Dict[str, bool]:
    """
    Get list of admin users (without passwords).
    Returns dict mapping username to exists status.
    """
    users = load_admin_users()
    return {username: True for username in users.keys()}