from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from .schemas import FeedbackResponse, FeedbackCreate
from .services import FeedbackService
from src.order.services import OrderService
from src.db.models import Customer
from src.auth.dependencies import get_current_customer
import uuid

feedback_router = APIRouter()
feedback_service = FeedbackService()
order_service = OrderService()

@feedback_router.post("/{order_id}", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_order_feedback(order_id: uuid.UUID, feedback: FeedbackCreate, current_customer: Customer = Depends(get_current_customer), session: AsyncSession = Depends(get_session)):
    db_order = await order_service.get_order(session, order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    feedback.customer_id = current_customer.customer_id
    feedback.order_id = order_id
    return await feedback_service.create_feedback(session, feedback)
