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


def require_auth(security_logger):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if user is None:
                security_logger.log_event(
                    event_type="AUTHENTICATION_FAILURE",
                    user_id="anonymous",
                    details="Invalid or missing session token",
                    severity="WARNING"
                )
                return jsonify({"error": "Authentication required"}), 401

            request.user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_role(security_logger, *allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = request.user

            if user["role"] not in allowed_roles:
                security_logger.log_event(
                    event_type="AUTHORIZATION_FAILURE",
                    user_id=user["username"],
                    details=f"Role '{user['role']}' not allowed. Required: {allowed_roles}",
                    severity="WARNING"
                )
                return jsonify({"error": "Forbidden"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator