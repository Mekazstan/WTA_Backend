from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import schemas, services, models
from database import get_db
from .utils import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

payment_router = APIRouter()

@payment_router.post("/", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(payment: schemas.PaymentCreate, db: AsyncSession = Depends(get_db)):
    # In a real scenario, you'd interact with a payment gateway here
    return await services.create_payment(db, payment)

@payment_router.get("/{payment_id}", response_model=schemas.PaymentResponse)
async def get_payment_details(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    payment = await services.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment