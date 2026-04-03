"""
Handles user registration and password verification.
Contains authentication-related business logic.
"""

import bcrypt
import time
import secrets
import hashlib

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
        "role": "guest",
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
        return {"error": "Username not found"}

    if is_account_locked(user):
        return {"error": "Account is temporarily locked"}

    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        reset_failed_attempts(user)
        return {"success": True, "user": user}

    record_failed_login(user)
    return {"error": "Invalid username or password"}

def promote_user(target_username):
    data = load_json(config.USERS_FILE)

    for user in data["users"]:
        if user["username"] == target_username:
            if user["role"] == "admin":
                return {"error": "Cannot change admin role"}
            if user["role"] == "user":
                return {"error": "User is already a user"}

            user["role"] = "user"
            save_json(config.USERS_FILE, data)
            return {"success": True, "message": f"{target_username} promoted to user"}

    return {"error": "User not found"}

def demote_user(target_username):
    data = load_json(config.USERS_FILE)

    for user in data["users"]:
        if user["username"] == target_username:
            if user["role"] == "admin":
                return {"error": "Cannot change admin role"}
            if user["role"] == "guest":
                return {"error": "User is already a guest"}

            user["role"] = "guest"
            save_json(config.USERS_FILE, data)
            return {"success": True, "message": f"{target_username} demoted to guest"}

    return {"error": "User not found"}

def get_user_from_username(username):
    user_data = load_json(config.USERS_FILE)
    for user in user_data.get("users", []):
        if user['username'] == username:
            return user
    return None

def get_user_from_email(email):
    data = load_json(config.USERS_FILE)
    for user in data["users"]:
        if user["email"].lower() == email.lower():
            return user
    return None


def load_password_resets():
    data = load_json(config.PASSWORD_RESETS_FILE)
    return data.get("resets", [])


def save_password_resets(resets):
    save_json(config.PASSWORD_RESETS_FILE, {"resets": resets})


def hash_reset_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_password_reset_token(email):
    user = get_user_from_email(email)
    if user is None:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(raw_token)

    resets = load_password_resets()
    resets.append({
        "username": user["username"],
        "email": user["email"],
        "token_hash": token_hash,
        "expires_at": time.time() + config.RESET_TOKEN_EXPIRY_SECONDS,
        "used": False,
        "created_at": time.time()
    })
    save_password_resets(resets)

    return {
        "username": user["username"],
        "email": user["email"],
        "token": raw_token
    }


def update_user_password(username, new_password):
    data = load_json(config.USERS_FILE)

    for user in data["users"]:
        if user["username"] == username:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)
            user["password_hash"] = hashed.decode('utf-8')

            if "failed_attempts" in user:
                user["failed_attempts"] = 0
            if "lockout_until" in user:
                user["lockout_until"] = 0

            save_json(config.USERS_FILE, data)
            return {"success": True}

    return {"error": "User not found"}


def reset_password_with_token(raw_token, new_password):
    token_hash = hash_reset_token(raw_token)
    resets = load_password_resets()

    for reset in resets:
        if reset["token_hash"] == token_hash:
            if reset["used"]:
                return {"error": "Token already used"}

            if time.time() > reset["expires_at"]:
                return {"error": "Token expired"}

            result = update_user_password(reset["username"], new_password)
            if "error" in result:
                return result

            reset["used"] = True
            reset["used_at"] = time.time()
            save_password_resets(resets)

            return {
                "success": True,
                "username": reset["username"]
            }

    return {"error": "Invalid token"}

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

def get_all_users():
    data = load_json(config.USERS_FILE)
    return data["users"]