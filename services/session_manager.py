"""
Handles session creation, validation, and expiration.
"""

import secrets
import time

from flask import request
from services.storage import load_json, save_json
import config


class SessionManager:
    def __init__(self, timeout=1800, bind_ip=True, bind_user_agent=True):  # 30 min
        self.timeout = timeout
        self.bind_ip = bind_ip
        self.bind_user_agent = bind_user_agent
        self.sessions_file = config.SESSIONS_FILE

    def load_sessions(self):
        data = load_json(self.sessions_file)
        return data.get("sessions", {})
    
    def save_sessions(self, sessions):
        save_json(self.sessions_file, {"sessions": sessions})

    def get_client_ip(self):
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.remote_addr or "unknown"

    def create_session(self, username):
        self.remove_all_expired_sessions()
        # generate session ID
        token = secrets.token_urlsafe(32)

        session = {
            'token': token,
            'username': username,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': self.get_client_ip(),
            'user_agent': request.headers.get("User-Agent", "")
        }

        sessions = self.load_sessions()
        sessions[token] = session
        self.save_sessions(sessions)

        return token

    def validate_session(self, token):
        sessions = self.load_sessions()

        session = sessions.get(token)
        if not session:
            return None
        
        if time.time() - session['last_activity'] > self.timeout:
            self.destroy_session(token)
            return None
        
        current_ip = self.get_client_ip()
        current_user_agent = request.headers.get("User-Agent", "")

        if self.bind_ip and session.get("ip_address") != current_ip:
            self.destroy_session(token)
            return None

        if self.bind_user_agent and session.get("user_agent") != current_user_agent:
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

    def remove_all_expired_sessions(self):
        sessions = self.load_sessions()
        current_time = time.time()

        active_sessions = {}

        for token, session in sessions.items():
            last_activity = session.get("last_activity", 0)
            if current_time - last_activity <= self.timeout:
                active_sessions[token] = session

        self.save_sessions(active_sessions)

    def destroy_user_sessions(self, username):
        sessions = self.load_sessions()

        sessions = {
            token: session
            for token, session in sessions.items()
            if session.get("username") != username
        }

        self.save_sessions(sessions)