from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, select
import logging
from uuid import UUID
from typing import List
from db.models import Customer
from .schemas import CustomerCreate, CustomerUpdate
from auth.utils import generate_password_hash

class CustomerService:

    async def get_customer_by_email(self, session: AsyncSession, email: str):
        try:
            stmt = select(Customer).where(Customer.email == email)
            result = await session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logging.error(f"Error getting user by email: {e}")
            return None

    async def get_customer_by_id(self, session: AsyncSession, customer_id: UUID):
        stmt = select(Customer).where(Customer.customer_id == customer_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create_customer(self, session: AsyncSession, customer: CustomerCreate) -> Customer:
        hashed_password = generate_password_hash(customer.password)
        db_customer = Customer(
            email=customer.email,
            password_hash=hashed_password,
            first_name=customer.first_name,
            last_name=customer.last_name,
            address=customer.address,
            contact_number=customer.contact_number
        )
        session.add(db_customer)
        await session.commit()
        await session.refresh(db_customer)
        return db_customer

    async def update_customer(self, session: AsyncSession, customer_id: UUID, customer_update: CustomerUpdate):
        db_customer = await self.get_customer_by_id(session, customer_id)
        if db_customer:
            update_data = customer_update.dict(exclude_unset=True)
            if "password" in update_data:
                update_data["password_hash"] = generate_password_hash(update_data["password"])
                del update_data["password"]
            await session.execute(update(Customer).where(Customer.customer_id == customer_id).values(**update_data))
            await session.commit()
            await session.refresh(db_customer)
        return db_customer

    async def delete_customer(self, session: AsyncSession, customer_id: UUID) -> bool:
        result = await session.execute(delete(Customer).where(Customer.customer_id == customer_id))
        await session.commit()
        return result.rowcount > 0

    async def list_customers(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Customer]:
        result = await session.execute(select(Customer).offset(skip).limit(limit))
        return result.scalars().all()