# app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.db.database import get_db
from app.schemas.user import UserLogin
from app.utils.jwt import create_access_token
from app.models.models import Usuario
from app.utils.crypto import verify_password

router = APIRouter()

@router.post("/login")
async def login(user: UserLogin, db: Annotated[Session, Depends(get_db)]):
    db_user = db.query(Usuario).filter(Usuario.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token_data = {
        "id": db_user.id,
        "sub": db_user.email,
        "role": db_user.tipo
    }
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}
