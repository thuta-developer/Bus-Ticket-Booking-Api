from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# ============================================
# 1. Password Hashing (Bcrypt)
# ============================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",  # Auto migrate old hashes if needed
    bcrypt__rounds=12,  # Work factor (12 is secure and fast enough)
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: The password provided by the user
        hashed_password: The bcrypt hash stored in the database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hashed password string
    """
    return pwd_context.hash(password)

# ============================================
# 2. JWT Token Utilities
# ============================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT Access Token (short-lived).
    
    Args:
        data: Dictionary containing user claims (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT Refresh Token (longer-lived).
    
    Args:
        data: Dictionary containing user claims (e.g., {"sub": user_id})
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token : str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
    
    
def get_token_data(token: str) -> Optional[Dict[str, Any]]:
    """
    Wrapper around decode_token to get token data.
    Raises specific exceptions if needed, but returns None on failure.
    """
    return decode_token(token)
