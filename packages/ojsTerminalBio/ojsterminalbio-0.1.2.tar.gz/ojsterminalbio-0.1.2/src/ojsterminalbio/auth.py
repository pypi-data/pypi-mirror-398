"""
Ranbir Portfolio CMS - Authentication
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
from .database import get_db
from .models.user import User

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return email"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from token or cookie"""
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    
    # Try cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    email = verify_token(token)
    if not email:
        return None
    
    user = db.query(User).filter(User.email == email).first()
    return user


def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authenticated user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not user.verify_password(password):
        return None
    return user
