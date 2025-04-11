from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import uuid
from db.main import get_session
from .services import PaymentService
from .schemas import PaymentCreate, PaymentResponse

logger = logging.getLogger(__name__)

payment_router = APIRouter()
payment_services = PaymentService()

@payment_router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(payment: PaymentCreate, session: AsyncSession = Depends(get_session)):
    try:
        # Interact with a payment gateway here
        return await payment_services.create_payment(session, payment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )

@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_details(payment_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    try:
        payment = await payment_services.get_payment(session, payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        return payment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving payment {payment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment details"
        )