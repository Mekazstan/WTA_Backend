from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from db.models import AdminUser
from auth.utils import generate_password_hash
from .schemas import AdminUserCreate


class AdminService:
    
    async def get_admin_user_by_email(self, session: AsyncSession, email: str) -> AdminUser | None:
        try:
            result = await session.execute(select(AdminUser).where(AdminUser.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logging.error(f"Database error while fetching admin user by email {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while fetching admin user"
            )
        except Exception as e:
            logging.error(f"Unexpected error while fetching admin user by email {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    async def create_admin_user(self, session: AsyncSession, admin_user: AdminUserCreate) -> AdminUser:
        try:
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
        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Database error while creating admin user {admin_user.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while creating admin user"
            )
        except ValueError as e:
            await session.rollback()
            logging.error(f"Value error while creating admin user {admin_user.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await session.rollback()
            logging.error(f"Unexpected error while creating admin user {admin_user.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while creating admin user"
            )
            
