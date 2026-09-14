import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import Config

_fernet_instance = None

def get_fernet():
    global _fernet_instance
    if _fernet_instance is None:
        key = Config.ENCRYPTION_KEY or os.getenv('ENCRYPTION_KEY') or "mSdaBjFzOZucluHVQ6neqbrlpg7U6K-LECf0XPQWqtA="
        if isinstance(key, str):
            key = key.encode()
        _fernet_instance = Fernet(key)
    return _fernet_instance

def encrypt_message(plaintext: str) -> str:
    if not plaintext:
        return ""
    f = get_fernet()
    encrypted = f.encrypt(plaintext.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted).decode('utf-8')

def decrypt_message(ciphertext) -> str:
    if not ciphertext:
        return ""
    try:
        if isinstance(ciphertext, bytes):
            ciphertext = ciphertext.decode('utf-8', errors='ignore')
            
        f = get_fernet()
        if ciphertext.startswith('Z0FBQUFB'):
            decoded = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted = f.decrypt(decoded)
            return decrypted.decode('utf-8')
        elif ciphertext.startswith('gAAAAA'):
            decrypted = f.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        else:
            return ciphertext
    except Exception:
        return "[Encrypted Message]"

def hash_file(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def hash_answer(answer: str) -> str:
    return hashlib.sha256(answer.strip().lower().encode()).hexdigest()

def verify_answer(answer: str, hashed: str) -> bool:
    if not hashed:
        return False
    if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
        try:
            from flask_bcrypt import Bcrypt
            b = Bcrypt()
            return b.check_password_hash(hashed, answer.strip()) or b.check_password_hash(hashed, answer.strip().lower())
        except Exception:
            pass
    return hash_answer(answer) == hashed
