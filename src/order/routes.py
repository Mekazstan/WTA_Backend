from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from .services import OrderService
from .schemas import OrderCreate, OrderResponse
from src.db.models import Customer
from src.db.main import get_session
from src.auth.dependencies import get_current_customer


order_router = APIRouter()
order_service = OrderService()

@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_new_order(order: OrderCreate, current_customer: Customer = Depends(get_current_customer), db: AsyncSession = Depends(get_session)):
    order.customer_id = current_customer.customer_id
    return await order_service.create_order(db, order)

