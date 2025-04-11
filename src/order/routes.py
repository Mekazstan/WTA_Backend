from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import schemas, services, models
from database import get_db
from .utils import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

order_router = APIRouter()

@order_router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_new_order(order: schemas.OrderCreate, current_customer: models.Customer = Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    order.customer_id = current_customer.customer_id
    return await services.create_order(db, order)

