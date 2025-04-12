from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from db.main import get_session
from db.models import Customer
from db.mongo import add_jti_to_blocklist
from auth.utils import create_access_tokens, verify_password
from order.schemas import OrderResponse
from order.services import OrderService
from .services import CustomerService
from .schemas import CustomerCreate, CustomerLogin, CustomerUpdate, CustomerResponse
from typing import List
from datetime import timedelta, datetime
from auth.dependencies import get_current_customer, RefreshTokenBearer, AccessTokenBearer

REFRESH_TOKEN_EXPIRY = 2
customer_router = APIRouter()
customer_service = CustomerService()
order_service = OrderService()

logger = logging.getLogger(__name__)

# --- Customer Authentication ---

@customer_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_customer_account(
    customer_create_data: CustomerCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        email = customer_create_data.email
        customer_exists = await customer_service.get_customer_by_email(session, email)
        if customer_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"A customer with email {email} already exists.",
            )

        new_customer = await customer_service.create_customer(session, customer_create_data)

        return new_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the customer account."
        )
    finally:
        await session.close()


@customer_router.post("/login", status_code=status.HTTP_200_OK)
async def login_customer(
    customer_login_data: CustomerLogin, session: AsyncSession = Depends(get_session)
):
    try:
        email = customer_login_data.email
        password = customer_login_data.password

        customer_account = await customer_service.get_customer_by_email(session, email)
        if customer_account is not None:
            password_valid = verify_password(password, customer_account.password_hash)

            if password_valid:
                access_token = create_access_tokens(
                    user_data={
                        "email": customer_account.email,
                        "customer_id": str(customer_account.customer_id)
                    }
                )

                refresh_token = create_access_tokens(
                    user_data={
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
                        "new_user": {
                            "email": customer_account.email,
                            "customer_id": str(customer_account.customer_id)
                        },
                    }
                )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Email or Password",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during customer login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login."
        )
    finally:
        await session.close()

@customer_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    try:
        expiry_timestamp = token_details['exp']
        if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
            new_access_token = create_access_tokens(user_data=token_details['user'])
            return JSONResponse(content={"access_token": new_access_token})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or Expired Token"
        )
    except HTTPException:
        raise
    except KeyError as e:
        logger.error(f"Missing key in token details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while refreshing token"
        )


@customer_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    try:
        jti = token_details["jti"]
        await add_jti_to_blocklist(jti)

        return JSONResponse(
            content={"message": "Logged out Successfully"},
            status_code=status.HTTP_200_OK,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


# --- Customer Profile Management ---
@customer_router.get("/profile", response_model=CustomerResponse)
async def get_customer_profile(current_customer: Customer = Depends(get_current_customer)):
    try:
        return current_customer
    except Exception as e:
        logger.error(f"Error fetching customer profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching profile"
        )

@customer_router.patch("/profile", response_model=CustomerResponse)
async def update_customer_profile(
    customer_update: CustomerUpdate,
    current_customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session)
):
    try:
        updated_customer = await customer_service.update_customer(
            session, current_customer.customer_id, customer_update
        )
        if not updated_customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return updated_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )
    finally:
        await session.close()

@customer_router.get("/orders", response_model=List[OrderResponse])
async def get_customer_order_history(
    current_customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    try:
        return await order_service.list_customer_orders(
            session, current_customer.customer_id, skip=skip, limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching orders"
        )
    finally:
        await session.close()
        