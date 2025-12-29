# src/xenfra/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet

from xenfra.config import settings

# --- Configuration ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# This key MUST be 32 url-safe base64-encoded bytes.
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

# --- Password Hashing ---
# Explicitly use passlib.backends.bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt passwords cannot be longer than 72 bytes. Truncate if necessary.
    # Note: Frontend should also enforce password length limits.
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

# --- JWT Handling ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# --- Token Encryption ---
def encrypt_token(token: str) -> str:
    """Encrypts a token using Fernet symmetric encryption."""
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts a token."""
    return fernet.decrypt(encrypted_token.encode()).decode()
