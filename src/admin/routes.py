from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional
from datetime import timedelta, datetime
from .schemas import AdminUserLogin, AdminUserCreate
from .services import AdminService
from customer.services import CustomerService
from customer.schemas import CustomerResponse, CustomerCreate, CustomerUpdate
from driver.services import DriverService
from driver.schemas import DriverResponse, DriverCreate, DriverUpdate
from order.services import OrderService
from order.schemas import OrderResponse, OrderAssign, OrderUpdate, OrderStatusUpdate
from db.main import get_session
from db.mongo import add_jti_to_blocklist
from auth.utils import create_access_tokens, verify_password
from auth.dependencies import RefreshTokenBearer, AccessTokenBearer, require_role

REFRESH_TOKEN_EXPIRY = 2
admin_router = APIRouter()
admin_service = AdminService()
customer_service = CustomerService()
driver_service = DriverService()
order_service = OrderService()

# --- Admin Authentication ---
@admin_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_admin_account(
    admin_create_data: AdminUserCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        email = admin_create_data.email
        admin_exists = await admin_service.get_admin_user_by_email(session, email)
        if admin_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"An Admin with email {email} already exists.",
            )

        new_admin = await admin_service.create_admin_user(session, admin_create_data)

        return {
            "message": "Admin Account Created.",
            "user": new_admin,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        await session.close()


@admin_router.post("/login", status_code=status.HTTP_200_OK)
async def login_admin(
    admin_login_data: AdminUserLogin, session: AsyncSession = Depends(get_session)
):
    try:
        email = admin_login_data.email
        username = admin_login_data.username
        password = admin_login_data.password

        admin_user = await admin_service.get_admin_user_by_email(session, email)
        if admin_user is not None:
            password_valid = verify_password(password, admin_user.password_hash)

            if password_valid:
                access_token = create_access_tokens(
                    user_data={
                        "email": admin_user.email,
                        "admin_id": str(admin_user.admin_id),
                        "role": "admin"
                    }
                )

                refresh_token = create_access_tokens(
                    user_data={
                        "email": admin_user.email,
                        "admin_id": str(admin_user.admin_id),
                        "role": "admin"
                    },
                    refresh=True,
                    expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
                )
                return JSONResponse(
                    content={
                        "message": "Login Successful",
                        "access token": access_token,
                        "refresh token": refresh_token,
                        "admin_user": {
                            "email": admin_user.email,
                            "uid": str(admin_user.admin_id),
                            "username": admin_user.username,
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        await session.close()


@admin_router.get("/refresh_token")
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@admin_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    try:
        jti = token_details["jti"]
        await add_jti_to_blocklist(jti)

        return JSONResponse(
            content={"message": "Logged out Successfully"},
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error during logout: {str(e)}"
        )

# --- Admin User Management ---
@admin_router.get("/customers", response_model=List[CustomerResponse], dependencies=[Depends(require_role(["admin"]))])
async def list_all_customers(session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100):
    try:
        customers = await customer_service.list_customers(session, skip=skip, limit=limit)
        return customers
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching customers: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.get("/customers/{customer_id}", response_model=CustomerResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_customer_by_admin(customer_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    try:
        customer = await customer_service.get_customer_by_id(session, customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching customer: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin"]))])
async def add_new_customer_by_admin(customer: CustomerCreate, session: AsyncSession = Depends(get_session)):
    try:
        db_customer = await customer_service.get_customer_by_email(session, customer.email)
        if db_customer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        return await customer_service.create_customer(session, customer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.patch("/customers/{customer_id}", response_model=CustomerResponse, dependencies=[Depends(require_role(["admin"]))])
async def update_customer_by_admin(customer_id: uuid.UUID, customer_update: CustomerUpdate, session: AsyncSession = Depends(get_session)):
    try:
        updated_customer = await customer_service.update_customer(session, customer_id, customer_update)
        if not updated_customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return updated_customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating customer: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
async def deactivate_customer_by_admin(customer_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    try:
        deleted = await customer_service.delete_customer(session, customer_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting customer: {str(e)}"
        )
    finally:
        await session.close()

# --- Admin Driver Management ---
@admin_router.get("/drivers", response_model=List[DriverResponse], dependencies=[Depends(require_role(["admin"]))])
async def list_all_drivers(session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100):
    try:
        drivers = await driver_service.list_drivers(session, skip=skip, limit=limit)
        return drivers
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching drivers: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.get("/drivers/{driver_id}", response_model=DriverResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_driver_by_admin(driver_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    try:
        driver = await driver_service.get_driver_by_id(session, driver_id)
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        return driver
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching driver: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def add_new_driver_by_admin(driver: DriverCreate, session: AsyncSession = Depends(get_session)):
    try:
        db_driver = await driver_service.get_driver_by_contact(session, driver.contact_number)
        if db_driver:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver with this contact number already exists")
        return await driver_service.create_driver(session, driver)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating driver: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.patch("/drivers/{driver_id}", response_model=DriverResponse, dependencies=[Depends(require_role(["admin"]))])
async def update_driver_by_admin(driver_id: uuid.UUID, driver_update: DriverUpdate, session: AsyncSession = Depends(get_session)):
    try:
        updated_driver = await driver_service.update_driver(session, driver_id, driver_update)
        if not updated_driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        return updated_driver
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating driver: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.delete("/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
async def deactivate_driver_by_admin(driver_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    try:
        deleted = await driver_service.delete_driver(session, driver_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting driver: {str(e)}"
        )
    finally:
        await session.close()

# --- Admin Order Management ---
@admin_router.get("/orders", response_model=List[OrderResponse], dependencies=[Depends(require_role(["admin"]))])
async def list_all_orders_by_admin(session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100, status: Optional[str] = None):
    try:
        orders = await order_service.list_orders(session, skip=skip, limit=limit, status=status)
        return orders
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching orders: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.get("/orders/{order_id}", response_model=OrderResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_order_by_admin(order_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    try:
        order = await order_service.get_order(session, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching order: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.patch("/orders/{order_id}/assign", response_model=OrderResponse, dependencies=[Depends(require_role(["admin"]))])
async def assign_order_to_driver(order_id: uuid.UUID, order_assign: OrderAssign, session: AsyncSession = Depends(get_session)):
    try:
        db_order = await order_service.get_order(session, order_id)
        db_driver = await order_service.get_driver_by_id(session, order_assign.driver_id)
        if not db_order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if not db_driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        updated_order = await order_service.update_order(session, order_id, OrderUpdate(assigned_driver_id=order_assign.driver_id, delivery_status="Assigned"))
        return updated_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning order: {str(e)}"
        )
    finally:
        await session.close()

@admin_router.patch("/orders/{order_id}/status", response_model=OrderResponse, dependencies=[Depends(require_role(["admin"]))])
async def update_order_delivery_status(order_id: uuid.UUID, status_update: OrderStatusUpdate, session: AsyncSession = Depends(get_session)):
    try:
        db_order = await order_service.get_order(session, order_id)
        if not db_order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        updated_order = await order_service.update_order(session, order_id, OrderUpdate(delivery_status=status_update.delivery_status))
        return updated_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating order status: {str(e)}"
        )
    finally:
        await session.close()
        
        