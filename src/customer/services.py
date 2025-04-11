from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, select
from uuid import UUID
from typing import List
from src.db.models import Customer
from schemas import CustomerCreate, CustomerUpdate
from src.auth.utils import generate_password_hash

class CustomerService:

    async def get_customer_by_email(self, db: AsyncSession, email: str) -> Customer | None:
        result = await db.execute(select(Customer).where(Customer.email == email))
        return result.scalar_one_or_none()

    async def get_customer_by_id(self, db: AsyncSession, customer_id: UUID) -> Customer | None:
        result = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
        return result.scalar_one_or_none()

    async def create_customer(self, db: AsyncSession, customer: CustomerCreate) -> Customer:
        hashed_password = generate_password_hash(customer.password)
        db_customer = Customer(
            email=customer.email,
            password_hash=hashed_password,
            first_name=customer.first_name,
            last_name=customer.last_name,
            address=customer.address,
            contact_number=customer.contact_number
        )
        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        return db_customer

    async def update_customer(self, db: AsyncSession, customer_id: UUID, customer_update: CustomerUpdate) -> Customer | None:
        db_customer = await self.get_customer_by_id(db, customer_id)
        if db_customer:
            update_data = customer_update.dict(exclude_unset=True)
            if "password" in update_data:
                update_data["password_hash"] = generate_password_hash(update_data["password"])
                del update_data["password"]
            await db.execute(update(Customer).where(Customer.customer_id == customer_id).values(**update_data))
            await db.commit()
            await db.refresh(db_customer)
        return db_customer

    async def delete_customer(self, db: AsyncSession, customer_id: UUID) -> bool:
        result = await db.execute(delete(Customer).where(Customer.customer_id == customer_id))
        await db.commit()
        return result.rowcount > 0

    async def list_customers(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Customer]:
        result = await db.execute(select(Customer).offset(skip).limit(limit))
        return result.scalars().all()