from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from .schemas import PaymentCreate
from db.models import Payment


class PaymentService:
    async def create_payment(self, session: AsyncSession, payment: PaymentCreate) -> Payment:
        db_payment = Payment(**payment.dict())
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return db_payment

    async def get_payment(self, session: AsyncSession, payment_id: UUID) -> Payment | None:
        result = await session.execute(select(Payment).where(Payment.payment_id == payment_id))
        return result.scalar_one_or_none()