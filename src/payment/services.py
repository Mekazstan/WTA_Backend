from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from typing import Optional
from uuid import UUID
from .schemas import PaymentCreate
from db.models import Payment

logger = logging.getLogger(__name__)


class PaymentService:
    async def create_payment(self, session: AsyncSession, payment: PaymentCreate) -> Payment:
        try:
            db_payment = Payment(**payment.dict())
            session.add(db_payment)
            await session.commit()
            await session.refresh(db_payment)
            return db_payment
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating payment: {str(e)}", exc_info=True)
            raise

    async def get_payment(self, session: AsyncSession, payment_id: UUID) -> Optional[Payment]:
        try:
            result = await session.execute(select(Payment).where(Payment.payment_id == payment_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}", exc_info=True)
            raise