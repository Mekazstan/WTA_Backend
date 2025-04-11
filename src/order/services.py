from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import List, Optional
from src.db.models import Order
from schemas import OrderCreate, OrderUpdate


class OrderService:
    async def create_order(self, db: AsyncSession, order: OrderCreate) -> Order:
        db_order = Order(**order.dict())
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)
        return db_order

    async def get_order(self, db: AsyncSession, order_id: UUID) -> Order | None:
        result = await db.execute(select(Order).where(Order.order_id == order_id))
        return result.scalar_one_or_none()

    async def list_customer_orders(self, db: AsyncSession, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        result = await db.execute(select(Order).where(Order.customer_id == customer_id).offset(skip).limit(limit))
        return result.scalars().all()

    async def list_orders(self, db: AsyncSession, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Order]:
        query = select(Order)
        if status:
            query = query.where(Order.delivery_status == status)
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def update_order(self, db: AsyncSession, order_id: UUID, order_update: OrderUpdate) -> Order | None:
        db_order = await self.get_order(db, order_id)
        if db_order:
            await db.execute(update(Order).where(Order.order_id == order_id).values(order_update.dict(exclude_unset=True)))
            await db.commit()
            await db.refresh(db_order)
        return db_order