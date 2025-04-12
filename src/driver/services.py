from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, select
import logging
from uuid import UUID
from typing import List
from db.models import Driver
from .schemas import DriverCreate, DriverUpdate
from auth.utils import generate_password_hash

logger = logging.getLogger(__name__)

class DriverService:

    async def get_driver_by_id(self, db: AsyncSession, driver_id: UUID) -> Driver | None:
        try:
            result = await db.execute(select(Driver).where(Driver.driver_id == driver_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting driver by ID {driver_id}: {str(e)}")
            raise

    async def get_driver_by_contact(self, db: AsyncSession, contact_number: str) -> Driver | None:
        try:
            result = await db.execute(select(Driver).where(Driver.contact_number == contact_number))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting driver by contact number {contact_number}: {str(e)}")
            raise

    async def create_driver(self, db: AsyncSession, driver: DriverCreate) -> Driver:
        try:
            hashed_password = generate_password_hash(driver.password)
            db_driver = Driver(
                name=driver.name,
                contact_number=driver.contact_number,
                vehicle_details=driver.vehicle_details.model_dump() if driver.vehicle_details else None,
                verification_status=driver.verification_status,
                password_hash=hashed_password,
                price_per_liter=driver.price_per_liter
            )
            db.add(db_driver)
            await db.commit()
            await db.refresh(db_driver)
            return db_driver
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating driver: {str(e)}")
            raise

    async def update_driver(self, db: AsyncSession, driver_id: UUID, driver_update: DriverUpdate) -> Driver | None:
        try:
            db_driver = await self.get_driver_by_id(db, driver_id)
            if db_driver:
                await db.execute(
                    update(Driver)
                    .where(Driver.driver_id == driver_id)
                    .values(driver_update.dict(exclude_unset=True))
                )
                await db.commit()
                await db.refresh(db_driver)
            return db_driver
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating driver {driver_id}: {str(e)}")
            raise

    async def delete_driver(self, db: AsyncSession, driver_id: UUID) -> bool:
        try:
            result = await db.execute(delete(Driver).where(Driver.driver_id == driver_id))
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting driver {driver_id}: {str(e)}")
            raise

    async def list_drivers(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Driver]:
        try:
            result = await db.execute(select(Driver).offset(skip).limit(limit))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing drivers: {str(e)}")
            raise
        