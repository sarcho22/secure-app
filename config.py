import os

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

BASE_URL = "https://127.0.0.1:5000"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
# created new gmail account and generated app password for testing...
SMTP_USERNAME = "secureappssc@gmail.com"
SMTP_PASSWORD = "lrtq aapn csml fkuh"
SMTP_FROM = SMTP_USERNAME

# Encryption
ENCRYPTION_KEY_FILE = os.path.join(DATA_DIR, "secret.key")

# Log file paths
LOG_DIR = os.path.join(BASE_DIR, "logs")
SECURITY_LOG = os.path.join(LOG_DIR, "security.log")
ACCESS_LOG = os.path.join(LOG_DIR, "access.log")

# "dev-secret-key" is default, can locally run 'export SECRET_KEY="secret"' before running app.py
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")