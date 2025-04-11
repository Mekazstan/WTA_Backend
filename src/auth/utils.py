from datetime import datetime, timedelta
from passlib.context import CryptContext
from config import Config
import logging
import jwt
import uuid


password_context = CryptContext(
    schemes=["bcrypt"]
)

ACCESS_TOKEN_EXPIRY = 3600

def generate_password_hash(password: str) -> str:
    hash = password_context.hash(password)
    
    return hash

def verify_password(password: str, hash: str) -> bool:
    return password_context.verify(password, hash)

def create_access_tokens(user_data: dict, expiry: timedelta = None, refresh: bool= False):
    payload = {}
    payload["user"] = user_data
    payload["exp"] = datetime.now() + (
            expiry if expiry is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        )
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh
    
    token = jwt.encode(
        payload= payload,
        key=Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM
    )
    return token

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None
