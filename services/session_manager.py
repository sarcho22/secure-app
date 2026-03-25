"""
Handles session creation, validation, and expiration.
"""

import secrets
import time

from flask import request
from services.storage import load_json, save_json
import config


class SessionManager:
    def __init__(self, timeout=1800): # 30 min
        self.timeout = timeout
        self.sessions_file = config.SESSIONS_FILE

    def load_sessions(self):
        data = load_json(self.sessions_file)
        return data.get("sessions", {})
    
    def save_sessions(self, sessions):
        save_json(self.sessions_file, {"sessions": sessions})

    def create_session(self, username):
        # generate session ID
        token = secrets.token_urlsafe(32)

        session = {
            'token': token,
            'username': username,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }

        sessions = self.load_sessions()
        sessions[token] = session
        self.save_sessions(sessions)

        return token

    def validate_session(self, token):
        sessions = self.load_sessions()

        if token not in sessions:
            return None
        
        session = sessions[token]
        if time.time() - session['last_activity'] > self.timeout:
            self.destroy_session(token)
            return None
        
        session['last_activity'] = time.time()
        sessions[token] = session
        self.save_sessions(sessions)

        return session


    def destroy_session(self, token):
        sessions = self.load_sessions()
        if token in sessions:
            del sessions[token]
            self.save_sessions(sessions)

    def destroy_user_sessions(self, username):
        data = load_json(config.SESSIONS_FILE)
        sessions = data.get("sessions", {})

        tokens_to_delete = []
        for token, session in sessions.items():
            if session.get("username") == username:
                tokens_to_delete.append(token)

        for token in tokens_to_delete:
            del sessions[token]

        save_json(config.SESSIONS_FILE, {"sessions": sessions})