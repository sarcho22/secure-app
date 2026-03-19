from functools import wraps
from flask import request, jsonify

from services.session_manager import SessionManager
from services.user_manager import get_user_from_username

session_manager = SessionManager()


def get_current_user():
    token = request.cookies.get("session_token")
    if not token:
        return None

    session = session_manager.validate_session(token)
    if not session:
        return None

    user = get_user_from_username(session["username"])
    return user


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return jsonify({"error": "Authentication required"}), 401

            if user["role"] != role:
                return jsonify({"error": "Forbidden"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator