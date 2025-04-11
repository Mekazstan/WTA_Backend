from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import AdminUser
from auth.utils import generate_password_hash
from .schemas import AdminUserCreate


class AdminService:
    
    async def get_admin_user_by_email(self, session: AsyncSession, email: str) -> AdminUser | None:
        result = await session.execute(select(AdminUser).where(AdminUser.email == email))
        return result.scalar_one_or_none()

    async def create_admin_user(self, session: AsyncSession, admin_user: AdminUserCreate) -> AdminUser:
        hashed_password = generate_password_hash(admin_user.password)
        db_admin_user = AdminUser(
            username=admin_user.username,
            email=admin_user.email,
            password_hash=hashed_password
        )
        session.add(db_admin_user)
        await session.commit()
        await session.refresh(db_admin_user)
        return db_admin_user