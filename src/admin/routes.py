from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.main import get_session
from typing import List
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
        password=hashed_password,
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
    staff_id: int, staff: StaffCreate, current_user: SuperAdmin = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    is_superadmin(current_user)
    result = await session.execute(select(Staff).where(Staff.id == staff_id))
    db_staff_member = result.scalars().first()
    if not db_staff_member:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Staff member not found")
    db_staff_member.first_name = staff.first_name
    db_staff_member.last_name = staff.last_name
    db_staff_member.email = staff.email
    db_staff_member.password = get_password_hash(staff.password)
    db_staff_member.created_by_id = current_user.id
    await session.commit()
    await session.refresh(db_staff_member)
    return db_staff_member
