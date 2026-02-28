"""
Handles user registration and password verification.
Contains authentication-related business logic.
"""

import bcrypt
import time

from services.validation import validate_username, validate_password_strength, validate_email
from services.storage import save_json
import config

def register_user(username, email, password):
    """
    - Hash password
    - Create user dict
    - Save to users.json
    """
    # Validate inputs
    if not validate_username(username):
        return {"error": "Invalid username"}
    
    if not validate_password_strength(password):
        return {"error": "Password does not meet requirements"}
    
    if not validate_email(email):
        return {"error": "Invalid email"}
    
    # Hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Store user (file-based)
    user = {
    "username": username,
    "email": email,
    "password_hash": hashed.decode('utf-8'),
    "created_at": time.time(),
    "role": "user",
    "failed_attempts": 0,
    "locked_until": None
    }

    save_json(config.USERS_FILE, user)
    return {"success": True}


def authenticate_user(username, password):
    """
    Paste login verification logic here.
    - hash password with bcrypt (cost factor >= 12)
    - never store plaintext passwords
    - Return user if valid
    """
    pass