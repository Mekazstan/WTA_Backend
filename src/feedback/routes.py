from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from db.main import get_session
from .schemas import FeedbackResponse, FeedbackCreate
from .services import FeedbackService
from order.services import OrderService
from db.models import Customer
from auth.dependencies import get_current_customer
import uuid

feedback_router = APIRouter()
feedback_service = FeedbackService()
order_service = OrderService()

logger = logging.getLogger(__name__)

@feedback_router.post("/{order_id}", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_order_feedback(
    order_id: uuid.UUID, 
    feedback: FeedbackCreate, 
    current_customer: Customer = Depends(get_current_customer), 
    session: AsyncSession = Depends(get_session)
):
    try:
        try:
            db_order = await order_service.get_order(session, order_id)
            if not db_order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
        except Exception as order_error:
            logger.error(f"Error fetching order {order_id}: {str(order_error)}")
            if isinstance(order_error, HTTPException):
                raise order_error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve order information"
            )
        customer_id = current_customer.customer_id
        try:
            print(f"Feedback: {feedback}")
            return await feedback_service.create_feedback(session, feedback, customer_id, order_id)
        except Exception as feedback_error:
            logger.error(f"Error creating feedback for order {order_id}: {str(feedback_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create feedback"
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(f"Unexpected error in create_order_feedback: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your feedback"
        )
