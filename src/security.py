from passlib.context import CryptContext
from cryptography.fernet import Fernet
import os
import base64
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Encryption setup
def _get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Generate a key if not provided, but warn that it's not persistent across restarts if not saved
        # Ideally, we should enforce ENCRYPTION_KEY in .env
        logger.warning("ENCRYPTION_KEY not set in environment. Generating a temporary key.")
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_value(value: str) -> str:
    if not value:
        return None
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    if not token:
        return None
    f = _get_fernet()
    try:
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None
