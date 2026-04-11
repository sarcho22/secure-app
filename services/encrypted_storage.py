from cryptography.fernet import Fernet
import json, config

class EncryptedStorage:
    def __init__(self):
        self.cipher = Fernet(config.FERNET_KEY)

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
    

    def encrypt_string(self, value):
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    
    def decrypt_string(self, value):
        return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")


# Usage:
# storage = EncryptedStorage()

# Save sensitive data
# storage.save_encrypted('data/passwords.enc', {
    # 'user1': {'site': 'example.com', 'password': 'encrypted_pass'}
# })

# Load sensitive data
# data = storage.load_encrypted('data/passwords.enc')

encrypted_storage = EncryptedStorage()