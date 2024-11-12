# app/utils/crypto.py

from bcrypt import hashpw, gensalt, checkpw

def hash_password(password: str) -> str:
    salt = gensalt()
    return hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode(), hashed_password.encode())
