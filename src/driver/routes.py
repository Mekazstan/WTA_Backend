from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from auth.utils import create_access_tokens, verify_password
from src.db.main import get_session
from src.db.models import Driver
from datetime import timedelta
from .schemas import DriverResponse, DriverCreate, DriverLogin, DriverUpdate
from .services import DriverService
from src.auth.dependencies import get_current_driver

REFRESH_TOKEN_EXPIRY = 2
driver_router = APIRouter()
driver_service = DriverService()

# --- Customer Authentication ---

@driver_router.post("/signup", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_account(
    driver_create_data: DriverCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        new_driver = await driver_service.create_driver(driver_create_data, session)

        return {
            "message": "Customer Account Created.",
            "new_driver": new_driver,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()


@driver_router.post("/login", status_code=status.HTTP_200_OK)
async def login_customer(
    driver_login_data: DriverLogin, session: AsyncSession = Depends(get_session)
):
    try:
        contact_number = driver_login_data.contact_number
        password = driver_login_data.password

        driver_account = await driver_service.get_driver_by_contact(contact_number, session)
        if driver_account is not None:
            password_valid = verify_password(password, driver_account.password_hash)

            if password_valid:
                access_token = create_access_tokens(
                    admin_data={
                        "contact_number": driver_account.contact_number,
                        "driver_id": str(driver_account.driver_id)
                    }
                )

                refresh_token = create_access_tokens(
                    admin_data={
                        "contact_number": driver_account.contact_number,
                        "driver_id": str(driver_account.driver_id)
                    },
                    refresh=True,
                    expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
                )
                return JSONResponse(
                    content={
                        "message": "Login Successful",
                        "access token": access_token,
                        "refresh token": refresh_token,
                        "driver": {
                            "contact_number": driver_account.contact_number,
                            "driver_id": str(driver_account.driver_id)
                        },
                    }
                )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Contact Details or Password",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()

# --- Driver Profile Management ---
@driver_router.get("/profile", response_model=DriverResponse)
async def get_driver_profile(current_driver: Driver = Depends(get_current_driver)):
    return current_driver

@driver_router.put("/profile", response_model=DriverResponse)
async def update_driver_profile(driver_update: DriverUpdate, current_driver: Driver = Depends(get_current_driver), db: AsyncSession = Depends(get_db)):
    updated_driver = await driver_service.update_driver(db, current_driver.driver_id, driver_update)
    if not updated_driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return updated_driver
