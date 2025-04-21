from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.main import get_session
from datetime import timedelta, datetime
from config import Config
from db.models import Customer, Staff, SuperAdmin

ACCESS_TOKEN_EXPIRE_MINUTES = 3600
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    return encoded_jwt

# Error Handling
def raise_http_exception(status_code: int, detail: str):
    raise HTTPException(status_code=status_code, detail=detail)


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        if user_id is None or user_type is None:
            raise credentials_exception
        try:
            user_id = int(user_id)
        except ValueError:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = None
    if user_type == "customer":
        result = await session.execute(select(Customer).where(Customer.id == user_id))
        user = result.scalars().first()
    elif user_type == "staff":
        result = await session.execute(select(Staff).where(Staff.id == user_id))
        user = result.scalars().first()
    elif user_type == "superadmin":
        result = await session.execute(select(SuperAdmin).where(SuperAdmin.id == user_id))
        user = result.scalars().first()
    else:
        raise credentials_exception

    if user is None:
        raise credentials_exception
    return user

#  Authorization:  Check user type and permissions
def is_staff_or_superadmin(current_user):
    if not isinstance(current_user, Staff) and not isinstance(current_user, SuperAdmin):
        raise_http_exception(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

def is_superadmin(current_user):
    if not isinstance(current_user, SuperAdmin):
        raise_http_exception(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.  Must be a superadmin.",
        )
    return current_user
