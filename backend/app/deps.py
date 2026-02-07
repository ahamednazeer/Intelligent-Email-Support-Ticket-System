from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from app.auth import decode_token
from app.repositories import users as user_repo
from app.schemas import UserResponse


def get_current_user(authorization: str | None = Header(default=None)) -> UserResponse:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = user_repo.get_user_by_username(username)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_roles(*roles: str):
    def _checker(user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user

    return _checker
