from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import schemas, services, models
from database import get_db
from .utils import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

customer_router = APIRouter()

# --- Utility Functions ---
async def get_current_customer(db: AsyncSession = Depends(get_db), token: str = Depends(OAuth2PasswordRequestForm)):
    # In a real application, you'd validate the token and retrieve the customer
    # This is a placeholder for authentication
    customer = await services.get_customer_by_email(db, token.username)
    if not customer or not verify_password(token.password, customer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return customer

# --- Customer Authentication ---
@customer_router.post("/register", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(customer: schemas.CustomerCreate, db: AsyncSession = Depends(get_db)):
    db_customer = await services.get_customer_by_email(db, customer.email)
    if db_customer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return await services.create_customer(db, customer)

@customer_router.post("/login", response_model=schemas.TokenResponse)
async def login_customer(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    customer = await services.get_customer_by_email(db, form_data.username)
    if not customer or not verify_password(form_data.password, customer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=30) # Adjust as needed
    access_token = create_access_token(data={"sub": customer.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# --- Customer Profile Management ---
@customer_router.get("/profile", response_model=schemas.CustomerResponse)
async def get_customer_profile(current_customer: models.Customer = Depends(get_current_customer)):
    return current_customer

@customer_router.put("/profile", response_model=schemas.CustomerResponse)
async def update_customer_profile(customer_update: schemas.CustomerUpdate, current_customer: models.Customer = Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    updated_customer = await services.update_customer(db, current_customer.customer_id, customer_update)
    if not updated_customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return updated_customer

@customer_router.get("/orders", response_model=List[schemas.OrderResponse])
async def get_customer_order_history(current_customer: models.Customer = Depends(get_current_customer), db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100):
    return await services.list_customer_orders(db, current_customer.customer_id, skip=skip, limit=limit)
