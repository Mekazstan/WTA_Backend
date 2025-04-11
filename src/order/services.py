from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging
from uuid import UUID
from typing import List, Optional
from db.models import Order
from .schemas import OrderCreate, OrderUpdate

logger = logging.getLogger(__name__)


class OrderService:
    async def create_order(self, db: AsyncSession, order: OrderCreate) -> Order:
        try:
            db_order = Order(**order.dict())
            db.add(db_order)
            await db.commit()
            await db.refresh(db_order)
            return db_order
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating order: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order"
            )

    async def get_order(self, db: AsyncSession, order_id: UUID) -> Order | None:
        try:
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch order {order_id}"
            )

    async def list_customer_orders(self, db: AsyncSession, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        try:
            result = await db.execute(
                select(Order)
                .where(Order.customer_id == customer_id)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing orders for customer {customer_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch orders for customer {customer_id}"
            )

    async def list_orders(self, db: AsyncSession, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Order]:
        try:
            query = select(Order)
            if status:
                query = query.where(Order.delivery_status == status)
            result = await db.execute(query.offset(skip).limit(limit))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing orders: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch orders"
            )

    async def update_order(self, db: AsyncSession, order_id: UUID, order_update: OrderUpdate) -> Order | None:
        try:
            db_order = await self.get_order(db, order_id)
            if db_order:
                await db.execute(
                    update(Order)
                    .where(Order.order_id == order_id)
                    .values(order_update.dict(exclude_unset=True))
                )
                await db.commit()
                await db.refresh(db_order)
            return db_order
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating order {order_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update order {order_id}"
            )
            