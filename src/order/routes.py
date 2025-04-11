from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import Optional
from .services import OrderService
from .schemas import OrderCreate, OrderResponse, OrderCancellationRequest
from db.models import Customer, Order
from db.main import get_session
from auth.dependencies import get_current_customer


order_router = APIRouter()
order_service = OrderService()

@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_new_order(order: OrderCreate, current_customer: Customer = Depends(get_current_customer), db: AsyncSession = Depends(get_session)):
    order.customer_id = current_customer.customer_id
    return await order_service.create_order(db, order)


@order_router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: uuid.UUID,
    cancellation_request: Optional[OrderCancellationRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user: Customer = Depends(get_current_customer)
):
    """
    Initiates the cancellation of a specific order.
    """
    db_order = await session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if db_order.customer_id != current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this order")

    # Update the order status to indicate cancellation request
    db_order.delivery_status = "Cancellation Requested"
    if cancellation_request and cancellation_request.reason:
        # You might want to store the cancellation reason in the order or a separate table
        print(f"Cancellation requested for order {order_id} by user {current_user.id}. Reason: {cancellation_request.reason}")
    else:
        print(f"Cancellation requested for order {order_id} by user {current_user.id}.")

    await session.commit()
    await session.refresh(db_order)

    # Here should trigger the notification (Send an email notification, to the team Slack channel)
    print(f"Admin notification triggered for order cancellation: {order_id}")

    return {"message": f"Cancellation request for order {order_id} initiated. We will contact you shortly."}

