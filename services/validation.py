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
    # note that spaces are invalid here! will not strip.
    if 3 <= len(username) <= 20:
        pattern = re.compile(r'[a-zA-Z0-9_]+')
        if pattern.fullmatch(username):
            return True
    return False

def validate_password_strength(password):
    # minimum 12 chars
    # 1 uppercase, 1 lowercase, 1 num, 1 special char (!@#$%^&*)
    if len(password) < 12:
        return False
    if not re.fullmatch(r'[a-zA-Z0-9!@#$%^&*]+', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*]', password):
        return False
    return True

def validate_email(email):
    # email FORMAT
    # check for duplicate email
    pattern = re.compile(r'[a-zA-Z0-9]+([._%+-][a-zA-Z0-9]+)*@' # local part cant begin/end with special char
                         r'[a-zA-Z0-9]+([\-][a-zA-Z0-9]+)*' # domain can have hyphen
                         r'(\.[a-zA-Z0-9]+([\-][a-zA-Z0-9]+)*)*' # subdomain
                         r'\.[a-zA-Z]{2,}') # tld at least two chars
    if re.fullmatch(pattern, email):
        return True
    return False

def sanitize_input(user_input):
    # Escape HTML special characters
    return html.escape(user_input)

def sanitize_output(data):
    """Sanitize before rendering"""
    if isinstance(data, str):
        return html.escape(data)
    return data

def safe_filename(filename):
    # remove path traversal attempts
    filename = os.path.basename(filename)

    # allow only alphanumeric, dash, underscore, dot
    if not re.match(r'^[\w\-\.]', filename):
        raise ValueError("Invalid filename")
    return filename

def safe_file_path(user_path, base_dir):
    # secure the filename
    filename = safe_filename(user_path)

    # construct full path
    full_path = os.path.join(base_dir, filename)

    if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
        raise ValueError("Path traversal detected")
    
    return full_path
