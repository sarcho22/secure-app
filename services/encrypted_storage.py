from cryptography.fernet import Fernet
import json

class EncryptedStorage:
    def __init__(self, key_file='secret.key'):
        # Load or generate encryption key
        try:
            with open(key_file, 'rb') as f:
                self.key = f.read()
        except FileNotFoundError:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)

        self.cipher = Fernet(self.key)

    def save_encrypted(self, filename, data):
        """Save encrypted JSON data"""
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())

        with open(filename, 'wb') as f:
            f.write(encrypted)

    def load_encrypted(self, filename):
        """Load and decrypt JSON data"""
        with open(filename, 'rb') as f:
            encrypted = f.read()

        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())


# Usage:
# storage = EncryptedStorage()

# Save sensitive data
# storage.save_encrypted('data/passwords.enc', {
    # 'user1': {'site': 'example.com', 'password': 'encrypted_pass'}
# })

# Load sensitive data
# data = storage.load_encrypted('data/passwords.enc')