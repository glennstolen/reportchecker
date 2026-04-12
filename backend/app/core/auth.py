from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.config import get_settings

ALGORITHM = "HS256"
MAGIC_TOKEN_EXPIRE_MINUTES = 15
SESSION_TOKEN_EXPIRE_DAYS = 7


def create_magic_token(email: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": email, "type": "magic", "exp": expire},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def create_session_token(email: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=SESSION_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": email, "type": "session", "exp": expire},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def verify_token(token: str, expected_type: str) -> Optional[str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """FastAPI dependency that returns the logged-in User or raises 401."""
    from app.models.user import User

    token = request.cookies.get("session")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ikke innlogget",
        )
    email = verify_token(token, "session")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller utløpt sesjon",
        )
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bruker ikke funnet",
        )
    return user
