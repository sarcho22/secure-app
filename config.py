import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from pathlib import Path
load_dotenv()

# Base directory of project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data storage paths
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.json")
PASSWORD_RESETS_FILE = os.path.join(DATA_DIR, "password_resets.json")

# reset password...
RESET_TOKEN_EXPIRY_SECONDS = 1800  # 30 minutes
RESET_REQUEST_COOLDOWN_SECONDS = 600 # 10 minutes

BASE_URL = "https://127.0.0.1:5000"

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USERNAME)

# Encryption key path
ENCRYPTION_KEY_FILE = os.path.join(DATA_DIR, "secret.key")

# Log file paths
LOG_DIR = os.path.join(BASE_DIR, "logs")
SECURITY_LOG = os.path.join(LOG_DIR, "security.log")
ACCESS_LOG = os.path.join(LOG_DIR, "access.log")

# used for signing session cookies / tokens
# "dev-secret-key" is default, can locally run 'export SECRET_KEY="secret"' before running app.py
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")


def get_fernet_key():
    key_path = Path(ENCRYPTION_KEY_FILE)
    if key_path.exists():
        return key_path.read_bytes().strip()
    
    # if doesnt exist, need to generate new one
    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    print("[KEY] Generated new encryption key (first run)")
    return key

# generate key if doesnt exist, otherwise return key
FERNET_KEY = get_fernet_key()