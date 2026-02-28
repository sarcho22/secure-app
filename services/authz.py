"""
Authorization decorators and role enforcement.
"""

# from functools import wraps


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if user['role'] != role:
                abort(403) # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Usage
# @app.route('/admin/dashboard')
# @require_auth
# @require_role('admin')
# def admin_dashboard():
#     return render_template('admin.html')