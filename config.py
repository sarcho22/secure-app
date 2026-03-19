import os

# Base directory of project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data storage paths
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

# Encryption
ENCRYPTION_KEY_FILE = os.path.join(DATA_DIR, "secret.key")

# Log file paths
LOG_DIR = os.path.join(BASE_DIR, "logs")
SECURITY_LOG = os.path.join(LOG_DIR, "security.log")
ACCESS_LOG = os.path.join(LOG_DIR, "access.log")

# Basic app settings 
DEBUG = True
# "dev-secret-key" is default, can locally run 'export SECRET_KEY="secret"' before running app.py
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")