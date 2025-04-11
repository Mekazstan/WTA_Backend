from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.db.models import Customer
from auth.utils import create_access_tokens, verify_password
from src.order.schemas import OrderResponse
from src.order.services import OrderService
from .services import CustomerService
from .schemas import CustomerCreate, CustomerResponse, CustomerLogin, CustomerUpdate
from typing import List
from datetime import timedelta
from src.auth.dependencies import get_current_customer

REFRESH_TOKEN_EXPIRY = 2
customer_router = APIRouter()
customer_service = CustomerService()
order_service = OrderService()

# --- Customer Authentication ---

@customer_router.post("/signup", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_account(
    customer_create_data: CustomerCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        email = customer_create_data.email
        customer_exists = await customer_service.get_customer_by_email(email, session)
        if customer_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"A customer with email {email} already exists.",
            )

        new_customer = await customer_service.create_customer(customer_create_data, session)

        return {
            "message": "Customer Account Created.",
            "new_customer": new_customer,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()


@customer_router.post("/login", status_code=status.HTTP_200_OK)
async def login_customer(
    customer_login_data: CustomerLogin, session: AsyncSession = Depends(get_session)
):
    try:
        email = customer_login_data.email
        password = customer_login_data.password

        customer_account = await customer_service.get_customer_by_email(email, session)
        if customer_account is not None:
            password_valid = verify_password(password, customer_account.password_hash)

            if password_valid:
                access_token = create_access_tokens(
                    admin_data={
                        "email": customer_account.email,
                        "customer_id": str(customer_account.customer_id)
                    }
                )

                refresh_token = create_access_tokens(
                    admin_data={
                        "email": customer_account.email,
                        "customer_id": str(customer_account.customer_id)
                    },
                    refresh=True,
                    expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
                )
                return JSONResponse(
                    content={
                        "message": "Login Successful",
                        "access token": access_token,
                        "refresh token": refresh_token,
                        "user": {
                            "email": customer_account.email,
                            "customer_id": str(customer_account.customer_id)
                        },
                    }
                )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Email or Password",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()

# --- Customer Profile Management ---
@customer_router.get("/profile", response_model=CustomerResponse)
async def get_customer_profile(current_customer: Customer = Depends(get_current_customer)):
    return current_customer

@customer_router.put("/profile", response_model=CustomerResponse)
async def update_customer_profile(customer_update: CustomerUpdate, current_customer: Customer = Depends(get_current_customer), session: AsyncSession = Depends(get_session)):
    updated_customer = await customer_service.update_customer(session, current_customer.customer_id, customer_update)
    if not updated_customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return updated_customer

@customer_router.get("/orders", response_model=List[OrderResponse])
async def get_customer_order_history(current_customer: Customer = Depends(get_current_customer), session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100):
    return await order_service.list_customer_orders(session, current_customer.customer_id, skip=skip, limit=limit)
