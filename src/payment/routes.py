from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from src.db.main import get_session
from .services import PaymentService
from .schemas import PaymentCreate, PaymentResponse


payment_router = APIRouter()
payment_services = PaymentService()

@payment_router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_session)):
    # Interact with a payment gateway here
    return await payment_services.create_payment(db, payment)

@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_details(payment_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    payment = await payment_services.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment