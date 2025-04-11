from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import schemas, services, models
from database import get_db
from .utils import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

feedback_router = APIRouter()

@feedback_router.post("/{order_id}", response_model=schemas.FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_order_feedback(order_id: UUID, feedback: schemas.FeedbackCreate, current_customer: models.Customer = Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    db_order = await services.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    feedback.customer_id = current_customer.customer_id
    feedback.order_id = order_id
    return await services.create_feedback(db, feedback)
