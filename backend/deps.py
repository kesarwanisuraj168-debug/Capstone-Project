"""Shared FastAPI dependencies: DB session + optional / required auth."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token


def raw_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    return authorization.replace("Bearer ", "").strip()


def optional_user(token: Optional[str] = Depends(raw_token),
                  db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_token(token)
        return db.query(User).filter(User.id == int(payload["sub"])).first()
    except Exception:
        return None


def require_user(user: Optional[User] = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator privileges required.")
    return user
