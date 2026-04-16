"""
Input validation and sanitization helpers.
whitelist validation (allow known good, not block known bad)
length limits on all inputs
sanitize file uploads (check extensions, MIME types, scan for malware)
"""

import html
import re
import os.path
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg"
}
# Expected starting bytes ("magic bytes") for allowed file types
FILE_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "txt": []  # no reliable universal magic bytes for plain text
}

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
    if len(password) < 12 or len(password) > 128:
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
    if len(email) > 254:
        return False
    
    # email FORMAT
    pattern = re.compile(r'[a-zA-Z0-9]+([._%+-][a-zA-Z0-9]+)*@' # local part cant begin/end with special char
                         r'[a-zA-Z0-9]+([\-][a-zA-Z0-9]+)*' # domain can have hyphen
                         r'(\.[a-zA-Z0-9]+([\-][a-zA-Z0-9]+)*)*' # subdomain
                         r'\.[a-zA-Z]{2,}') # tld at least two chars
    if re.fullmatch(pattern, email):
        return True
    return False

def sanitize_output(data):
    """Sanitize before rendering"""
    if isinstance(data, str):
        return html.escape(data)
    return data

def safe_filename(filename):
    # remove path traversal attempts
    if len(filename) > 255:
        raise ValueError("Filename too long")
    filename = os.path.basename(filename)
    filename = secure_filename(filename)

    if not filename:
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

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_mime_type(mime_type):
    return mime_type in ALLOWED_MIME_TYPES

# for text files, filter out binary files disguised with .txt extension
def is_likely_text_file(file_stream, sample_size=512):
    file_stream.seek(0)
    chunk = file_stream.read(sample_size)
    file_stream.seek(0)

    if b"\x00" in chunk:
        return False

    try:
        chunk.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

# check magic bytes for non-text files, and for text files check if they are likely text (not binary disguised as .txt)
def matches_file_signature(file_stream, filename):
    ext = filename.rsplit(".", 1)[1].lower()

    file_stream.seek(0)
    header = file_stream.read(16)
    file_stream.seek(0)

    # txt handled separately
    if ext == "txt":
        return is_likely_text_file(file_stream)

    valid_signatures = FILE_SIGNATURES.get(ext, [])
    return any(header.startswith(sig) for sig in valid_signatures)

# very basic scan for suspicious content patterns... 
# not real antivirus / malware detection... 
# only checks for few known strings in first 4096 bytes... 
# implemented with chatgpt
def scan_for_known_bad_signatures(file_stream):
    suspicious_patterns = [
        b"<script>",
        b"<?php",
        b"powershell",
        b"cmd.exe",
        b"/bin/sh"
    ]

    file_stream.seek(0)
    content = file_stream.read(4096).lower()
    file_stream.seek(0)

    return not any(pattern in content for pattern in suspicious_patterns)