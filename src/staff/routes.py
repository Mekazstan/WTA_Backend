from fastapi import APIRouter, Depends, status
from fastapi.security import security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from typing import List
from db.main import get_session
from jose import JWTError, jwt
from config import Config
from db.models import Staff, SuperAdmin, Order, Driver, OrderStatus, Customer
from order.schemas import OrderRead
from customer.schemas import CustomerRead
from driver.schemas import DriverRead, DriverCreate
from utils.helper_func import (raise_http_exception, get_password_hash, verify_password, 
                                   create_access_token, get_current_user, is_staff_or_superadmin)

staff_router = APIRouter()

@staff_router.post("/api/staff/login/")
async def login_staff(form_data: security.OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    # Check staff
    result = await session.execute(select(Staff).where(Staff.email == form_data.username))
    db_staff = result.scalars().first()
    
    if not db_staff or not verify_password(form_data.password, db_staff.password):
        # Check superadmin if staff not found
        result = await session.execute(select(SuperAdmin).where(SuperAdmin.email == form_data.username))
        db_superadmin = result.scalars().first()
        
        if not db_superadmin or not verify_password(form_data.password, db_superadmin.password):
            raise_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        else:
             access_token_data = {"sub": str(db_superadmin.id), "user_type": "superadmin"}
             access_token = create_access_token(access_token_data)
             return {"access_token": access_token, "token_type": "bearer", "user_type": "superadmin"}

    access_token_data = {"sub": str(db_staff.id), "user_type": "staff"}
    access_token = create_access_token(access_token_data)
    return {"access_token": access_token, "token_type": "bearer", "user_type": "staff"}

@staff_router.post("/api/admin/password/reset/request/")
async def request_staff_password_reset(email: EmailStr, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Staff).where(Staff.email == email))
    db_staff = result.scalars().first()
    
    if not db_staff:
        result = await session.execute(select(SuperAdmin).where(SuperAdmin.email == email))
        db_superadmin = result.scalars().first()
        if not db_superadmin:
            raise_http_exception(status.HTTP_404_NOT_FOUND, "Email not found")
        else:
             # Send email with reset link
             print(f"Super Admin Reset link sent to {email}")
             return {"message": "Password reset link sent to your email"}
    
    # Send email with reset link
    print(f"Staff Reset link sent to {email}")
    return {"message": "Password reset link sent to your email"}

@staff_router.post("/api/admin/password/reset/confirm/")
async def confirm_staff_password_reset(new_password: str, confirm_new_password: str, token: str, session: AsyncSession = Depends(get_session)):
    if new_password != confirm_new_password:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Passwords do not match")
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        if user_type not in ('staff', 'superadmin'):
            raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid Token")
    except JWTError:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid token")

    if user_type == "staff":
        result = await session.execute(select(Staff).where(Staff.id == user_id))
        db_staff = result.scalars().first()
        if not db_staff:
            raise_http_exception(status.HTTP_404_NOT_FOUND, "Staff not found")
        hashed_password = get_password_hash(new_password)
        db_staff.password = hashed_password
        await session.commit()
    elif user_type == "superadmin":
        result = await session.execute(select(SuperAdmin).where(SuperAdmin.id == user_id))
        db_superadmin = result.scalars().first()
        if not db_superadmin:
            raise_http_exception(status.HTTP_404_NOT_FOUND, "SuperAdmin not found")
        hashed_password = get_password_hash(new_password)
        db_superadmin.password = hashed_password
        await session.commit()

    return {"message": "Password reset successfully"}

@staff_router.get("/api/admin/orders/", response_model=List[OrderRead])
async def get_orders(current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Order))
    orders = result.scalars().all()
    return orders

@staff_router.get("/api/admin/orders/{order_id}/", response_model=OrderRead)
async def get_order(order_id: int, current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    return order

@staff_router.patch("/api/admin/orders/{order_id}/assign-driver/", response_model=OrderRead)
async def assign_driver_to_order(
    order_id: int,
    driver_id: int,
    current_user: Staff = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    
    result = await session.execute(select(Driver).where(Driver.id == driver_id))
    db_driver = result.scalars().first()
    if not db_driver:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Driver not found")
    
    db_order.driver_id = driver_id
    db_order.staff_assigned_id = current_user.id
    await session.commit()
    await session.refresh(db_order)
    return db_order

@staff_router.patch("/api/admin/orders/{order_id}/set-charge/", response_model=OrderRead)
async def set_driver_charge(
    order_id: int,
    driver_charge: float,
    current_user: Staff = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.PAIRING:
        raise_http_exception(
            status.HTTP_400_BAD_REQUEST, "Charge can only be set for orders in 'pairing' status"
        )
    db_order.driver_charge = driver_charge
    db_order.staff_assigned_id = current_user.id
    await session.commit()
    await session.refresh(db_order)
    return db_order

@staff_router.patch("/api/admin/orders/{order_id}/dispatch/", response_model=OrderRead)
async def dispatch_order(order_id: int, current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.PENDING_PAYMENT:
        raise_http_exception(
            status.HTTP_400_BAD_REQUEST, "Order must be in 'pending_payment' status to be dispatched"
        )
    db_order.status = OrderStatus.EN_ROUTE
    await session.commit()
    await session.refresh(db_order)
    return db_order

@staff_router.patch("/api/admin/orders/{order_id}/delivered/", response_model=OrderRead)
async def mark_order_as_delivered(
    order_id: int, current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.EN_ROUTE:
        raise_http_exception(
            status.HTTP_400_BAD_REQUEST, "Order must be 'en-route' to be marked as delivered"
        )
    db_order.status = OrderStatus.DELIVERED
    await session.commit()
    await session.refresh(db_order)
    return db_order

@staff_router.get("/api/admin/customers/", response_model=List[CustomerRead])
async def get_customers(current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Customer))
    customers = result.scalars().all()
    return customers

@staff_router.get("/api/admin/customers/{customer_id}/", response_model=CustomerRead)
async def get_customer(customer_id: int, current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Customer not found")
    return customer

@staff_router.post("/api/admin/drivers/", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
async def create_driver(driver: DriverCreate, current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    db_driver = Driver(
        first_name=driver.first_name,
        last_name=driver.last_name,
        phone_number=driver.phone_number,
        vehicle_details=driver.vehicle_details,
        is_active=driver.is_active
    )
    session.add(db_driver)
    await session.commit()
    await session.refresh(db_driver)
    return db_driver

@staff_router.get("/api/admin/drivers/", response_model=List[DriverRead])
async def get_drivers(current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Driver))
    drivers = result.scalars().all()
    return drivers

@staff_router.get("/api/admin/drivers/{driver_id}/", response_model=DriverRead)
async def get_driver(driver_id: int, current_user: Staff = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    is_staff_or_superadmin(current_user)
    result = await session.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalars().first()
    if not driver:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Driver not found")
    return driver

