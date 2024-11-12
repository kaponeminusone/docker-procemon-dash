# app/dependencies/auth.py

from fastapi import Depends, HTTPException, status, Request
from app.utils.jwt import verify_token

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
        )

    token = auth_header.split(" ")[1]  # Extraemos el token después de "Bearer"
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    print("????")

    return {
        "id": payload.get("id"),
        "email": payload.get("sub"),
        "role": payload.get("role")
    }
