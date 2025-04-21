from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from db.main import get_session
from typing import List
from .schemas import StaffUpdate
from db.models import Staff, SuperAdmin
from staff.schemas import StaffRead, StaffCreate
from utils.helper_func import (raise_http_exception, get_password_hash,
                                   get_current_user, is_superadmin)

admin_router = APIRouter()

@admin_router.post("/api/superadmin/staff/", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(staff: StaffCreate, current_user: SuperAdmin = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_superadmin(current_user)
    result = await session.execute(select(Staff).where(Staff.email == staff.email))
    db_staff = result.scalars().first()
    if db_staff:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Email already registered")
    hashed_password = get_password_hash(staff.password)
    db_staff = Staff(
        first_name=staff.first_name,
        last_name=staff.last_name,
        email=staff.email,
        hashed_password=hashed_password,
        created_by_id=current_user.id,
    )
    session.add(db_staff)
    await session.commit()
    await session.refresh(db_staff)
    return db_staff

@admin_router.get("/api/superadmin/staff/", response_model=List[StaffRead])
async def get_staff_members(current_user: SuperAdmin = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_superadmin(current_user)
    result = await session.execute(select(Staff))
    staff_members = result.scalars().all()
    return staff_members

@admin_router.get("/api/superadmin/staff/{staff_id}/", response_model=StaffRead)
async def get_staff_member(staff_id: int, current_user: SuperAdmin = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_superadmin(current_user)
    result = await session.execute(select(Staff).where(Staff.id == staff_id))
    staff_member = result.scalars().first()
    if not staff_member:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Staff member not found")
    return staff_member

@admin_router.patch("/api/superadmin/staff/{staff_id}/update/", response_model=StaffRead)
async def update_staff_member(
    staff_id: int,
    staff_update: StaffUpdate,
    current_user: SuperAdmin = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    is_superadmin(current_user)
    result = await session.execute(select(Staff).where(Staff.id == staff_id))
    db_staff_member = result.scalars().first()
    if not db_staff_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

    update_data = staff_update.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"] is not None:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    await session.execute(
        update(Staff)
        .where(Staff.id == staff_id)
        .values(update_data)
    )
    await session.commit()
    await session.refresh(db_staff_member)
    return db_staff_member
