from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from sqlalchemy import select
from typing import List
from datetime import datetime
from db.main import get_session
from jose import JWTError, jwt
from config import Config
from db.models import Customer, Order, OrderStatus, RecyclableSubmission, PaymentStatus
from order.schemas import OrderRead, OrderCreate
from recycle.schemas import RecyclableSubmissionRead, RecyclableSubmissionCreate
from utils.helper_func import (raise_http_exception, get_password_hash, verify_password, 
                                   create_access_token, get_current_user)
from .schemas import CustomerRead, CustomerCreate

customer_router = APIRouter()

@customer_router.post("/api/customers/register/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def register_customer(customer: CustomerCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == customer.email))
    db_customer = result.scalars().first()
    if db_customer:
        await raise_http_exception(status.HTTP_400_BAD_REQUEST, "Email already registered")
    hashed_password = get_password_hash(customer.password)
    db_customer = Customer(
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        hashed_password=hashed_password,
    )
    print("Here 3")
    session.add(db_customer)
    await session.commit()
    await session.refresh(db_customer)
    return db_customer

@customer_router.post("/api/customers/login/")
async def login_customer(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == form_data.username))
    db_customer = result.scalars().first()
    if not db_customer or not verify_password(form_data.password, db_customer.hashed_password):
        await raise_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    access_token_data = {"sub": str(db_customer.id), "user_type": "customer"}
    access_token = create_access_token(access_token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@customer_router.post("/api/customers/password/reset/request/")
async def request_customer_password_reset(email: EmailStr, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == email))
    db_customer = result.scalars().first()
    if not db_customer:
        await raise_http_exception(status.HTTP_404_NOT_FOUND, "Email not found")
    #  Send email with reset link (implementation depends on your email service)
    #  The reset link should contain a token (e.g., a short-lived JWT)
    print(f"Reset link sent to {email}") # Replace with actual email sending
    return {"message": "Password reset link sent to your email"}

@customer_router.post("/api/customers/password/reset/confirm/")
async def confirm_customer_password_reset(new_password: str, confirm_new_password: str, token: str, session: AsyncSession = Depends(get_session)):
    if new_password != confirm_new_password:
        await raise_http_exception(status.HTTP_400_BAD_REQUEST, "Passwords do not match")
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        if user_type != 'customer':
            await raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid Token")
    except JWTError:
        await raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid token")
    result = await session.execute(select(Customer).where(Customer.id == user_id))
    db_customer = result.scalars().first()
    if not db_customer:
        await raise_http_exception(status.HTTP_404_NOT_FOUND, "User not found")
    hashed_password = get_password_hash(new_password)
    db_customer.hashed_password = hashed_password
    await session.commit()
    return {"message": "Password reset successfully"}

@customer_router.post("/api/customers/orders/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, current_customer: Customer = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only create orders.")
    db_order = Order(
        customer_id=current_customer.id,
        destination_address=order.destination_address,
        water_amount=order.water_amount,
    )
    session.add(db_order)
    await session.commit()
    await session.refresh(db_order)
    return db_order

@customer_router.get("/api/customers/orders/", response_model=List[OrderRead])
async def get_customer_orders(current_customer: Customer = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own orders.")
    result = await session.execute(
        select(Order).where(Order.customer_id == current_customer.id)
    )
    orders = result.scalars().all()
    return orders

@customer_router.get("/api/customers/orders/{order_id}/", response_model=OrderRead)
async def get_customer_order(order_id: int, current_customer: Customer = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own order.")
    result = await session.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == current_customer.id)
    )
    order = result.scalars().first()
    if not order:
        await raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    return order

@customer_router.patch("/api/customers/orders/{order_id}/cancel/", response_model=OrderRead)
async def cancel_order(order_id: int, current_customer: Customer = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only cancel their own orders.")
    result = await session.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == current_customer.id)
    )
    db_order = result.scalars().first()
    if not db_order:
        await raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.PAIRING:
        await raise_http_exception(status.HTTP_400_BAD_REQUEST, "Order cannot be cancelled at this status")
    db_order.status = OrderStatus.CANCELLED
    await session.commit()
    await session.refresh(db_order)
    return db_order

@customer_router.post("/api/customers/recyclables/", response_model=RecyclableSubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_recyclable_submission(
    submission: RecyclableSubmissionCreate,
    current_customer: Customer = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only create recyclable submissions.")

    db_submission = RecyclableSubmission(
        customer_id=current_customer.id,
        image_url=submission.image_url,
        recyclable_type=submission.recyclable_type,
        pickup_option=submission.pickup_option,
        pickup_address=submission.pickup_address,
        dropoff_location=submission.dropoff_location,
    )
    session.add(db_submission)
    await session.commit()
    await session.refresh(db_submission)
    return db_submission

@customer_router.get("/api/customers/recyclables/", response_model=List[RecyclableSubmissionRead])
async def get_customer_recyclable_submissions(
    current_customer: Customer = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own recyclable submissions.")
    result = await session.execute(
        select(RecyclableSubmission).where(RecyclableSubmission.customer_id == current_customer.id)
    )
    submissions = result.scalars().all()
    return submissions

@customer_router.get("/api/customers/recyclables/{submission_id}/", response_model=RecyclableSubmissionRead)
async def get_customer_recyclable_submission(
    submission_id: int,
    current_customer: Customer = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not isinstance(current_customer, Customer):
        await raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own recyclable submission.")
    result = await session.execute(
        select(RecyclableSubmission)
        .where(RecyclableSubmission.id == submission_id, RecyclableSubmission.customer_id == current_customer.id)
    )
    submission = result.scalars().first()
    if not submission:
        await raise_http_exception(status.HTTP_404_NOT_FOUND, "Recyclable submission not found")
    return submission

@customer_router.post("/api/customers/orders/{order_id}/accept-charge/")
async def accept_driver_charge(
    order_id: int,
    current_customer: Customer = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Accept the driver's charge for an order and update the order status.
    """
    result = await session.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == current_customer.id)
    )
    db_order = result.scalars().first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if db_order.status != OrderStatus.PAIRING:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not in 'pairing' status.  Current status is {db_order.status}",
        )

    if db_order.driver_charge is None:
        raise HTTPException(
            status_code=400, detail="Driver charge has not been set for this order."
        )
    #  Integrate with payment gateway
    #  Test simulation for a successful payment
    print(f"Simulating payment for order {order_id} for {db_order.driver_charge}")
    payment_successful = True

    if payment_successful:
        db_order.status = OrderStatus.PENDING_PAYMENT
        db_order.payment_status = PaymentStatus.PAID
        db_order.payment_date = datetime.utcnow()
        await session.commit()
        await session.refresh(db_order)
        return {"message": "Payment successful.  Awaiting dispatch.", "order": db_order}
    else:
        raise HTTPException(status_code=400, detail="Payment failed")
