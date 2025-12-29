import hashlib
import secrets

USERS = {}
TOKENS = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(username: str) -> str:
    token = secrets.token_hex(32)
    TOKENS[token] = username
    return token
