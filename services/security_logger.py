import logging
from flask import request
import json
from datetime import datetime
import os

class SecurityLogger:
    def __init__(self, log_file='logs/security.log'):
        self.log_file = log_file
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event_type, user_id, details, severity='INFO'):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'details': details,
            'severity': severity
        }

        message = json.dumps(log_entry)

        if severity == 'CRITICAL':
            self.logger.critical(message)
        elif severity == 'ERROR':
            self.logger.error(message)
        elif severity == 'WARNING':
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def read_logs(self, limit=200):
        if not os.path.exists(self.log_file):
            return []

        entries = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({
                    'timestamp': None,
                    'event_type': 'UNKNOWN',
                    'user_id': None,
                    'ip_address': None,
                    'user_agent': None,
                    'details': line,
                    'severity': 'INFO'
                })

            if len(entries) >= limit:
                break

        return entries