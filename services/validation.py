"""
Input validation and sanitization helpers.
whitelist validation (allow known good, not block known bad)
length limits on all inputs
type checking (integers, emails, URLs)
sanitize file uploads (check extensions, MIME types, scan for malware)
"""

import html
import re
import os.path
from werkzeug.utils import secure_filename


def validate_username(username):
    # 3-20 chars, alphanumeric + underscore
    # check for duplicate username
    return

def validate_password_strength(password):
    # minimum 12 chars
    # 1 uppercase, 1 lowercase, 1 num, 1 special char (!@#$%^&*)
    
    return

def validate_email(email):
    # email FORMAT
    # check for duplicate email
    return

def sanitize_input(user_input):
    """Escape HTML special characters"""
    return html.escape(user_input)

def sanitize_output(data):
    """Sanitize before rendering"""
    if isinstance(data, str):
        return html.escape(data)
    return data

def safe_filename(filename):
    return filename

def safe_file_path(user_path, base_dir):

    full_path = "insert code"
    return full_path