from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import schemas, services, models
from database import get_db
from .utils import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# --- Utility Functions ---
async def get_current_customer(db: AsyncSession = Depends(get_db), token: str = Depends(OAuth2PasswordRequestForm)):
    # In a real application, you'd validate the token and retrieve the customer
    # This is a placeholder for authentication
    customer = await services.get_customer_by_email(db, token.username)
    if not customer or not verify_password(token.password, customer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return customer

async def get_current_admin_user(db: AsyncSession = Depends(get_db), token: str = Depends(OAuth2PasswordRequestForm)):
    admin_user = await services.get_admin_user_by_username(db, token.username)
    if not admin_user or not verify_password(token.password, admin_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return admin_user


report_router = APIRouter()

# --- Admin Reporting ---
@report_router.get("/orders", response_model=schemas.OrderReportResponse)
async def get_orders_report(db: AsyncSession = Depends(get_db)):
    return await services.get_order_report(db)

@report_router.get("/revenue", response_model=schemas.RevenueReportResponse)
async def get_revenue_report_endpoint(db: AsyncSession = Depends(get_db)):
    return await services.get_revenue_report(db)

@report_router.get("/feedback", response_model=schemas.FeedbackReportResponse)
async def get_feedback_report_endpoint(db: AsyncSession = Depends(get_db)):
    return await services.get_feedback_report(db)