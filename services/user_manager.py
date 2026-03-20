"""
Handles user registration and password verification.
Contains authentication-related business logic.
"""

import bcrypt
import time

from services.validation import validate_username, validate_password_strength, validate_email
from services.storage import save_json, load_json
import config

MAX_FAILURES = 5
LOCKOUT_DURATION = 900 # 15 minutes

def register_user(username, email, password):
    # Validate inputs
    if not validate_username(username):
        return {"error": "Invalid username"}
    
    if not validate_password_strength(password):
        return {"error": "Password does not meet requirements"}
    
    if not validate_email(email):
        return {"error": "Invalid email"}
    
    if username_exists(username):
        return {"error": "Username already exists"}
    
    if email_exists(email):
        return {"error": "Email already associated with an account"}

    
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

    user_data = load_json(config.USERS_FILE)
    users = user_data.get("users", [])
    users.append(user)
    user_data["users"] = users

    save_json(config.USERS_FILE, user_data)
    return {"success": True}


def authenticate_user(username, password):
    user = get_user_from_username(username)
    if user is None:
        return {"error": "Invalid username or password"}

    if is_account_locked(user):
        return {"error": "Account is temporarily locked"}

    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        reset_failed_attempts(user)
        return {"success": True, "user": user}

    record_failed_login(user)
    return {"error": "Invalid username or password"}

def get_user_from_username(username):
    user_data = load_json(config.USERS_FILE)
    for user in user_data.get("users", []):
        if user['username'] == username:
            return user
    return None

def username_exists(username):
    return get_user_from_username(username) is not None

def email_exists(email):
    user_data = load_json(config.USERS_FILE)
    for user in user_data.get("users", []):
        if user['email'] == email:
            return True
    return False

def get_all_users():
    user_data = load_json(config.USERS_FILE)
    return user_data.get("users", [])


def save_all_users(users):
    save_json(config.USERS_FILE, {"users": users})


def update_user(updated_user):
    users = get_all_users()
    for i, user in enumerate(users):
        if user["username"] == updated_user["username"]:
            users[i] = updated_user
            save_all_users(users)
            return True
    return False


def is_account_locked(user):
    locked_until = user.get("locked_until")

    if locked_until is None:
        return False

    if time.time() >= locked_until:
        user["locked_until"] = None
        user["failed_attempts"] = 0
        update_user(user)
        return False

    return True


def reset_failed_attempts(user):
    user["failed_attempts"] = 0
    user["locked_until"] = None
    update_user(user)


def record_failed_login(user):
    user["failed_attempts"] += 1

    if user["failed_attempts"] >= MAX_FAILURES:
        user["locked_until"] = time.time() + LOCKOUT_DURATION
        user["failed_attempts"] = 0

    update_user(user)