from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from auth.utils import create_access_tokens, verify_password
from db.mongo import add_jti_to_blocklist
from db.main import get_session
from db.models import Driver
from datetime import timedelta, datetime
from .schemas import DriverResponse, DriverCreate, DriverLogin, DriverUpdate
from .services import DriverService
from auth.dependencies import get_current_driver, RefreshTokenBearer, AccessTokenBearer

REFRESH_TOKEN_EXPIRY = 2
driver_router = APIRouter()
driver_service = DriverService()

# --- Customer Authentication ---

@driver_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_driver_account(
    driver_create_data: DriverCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        new_driver = await driver_service.create_driver(session, driver_create_data)

        return {
            "message": "Customer Account Created.",
            "new_driver": new_driver,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()


@driver_router.post("/login", status_code=status.HTTP_200_OK)
async def login_driver(
    driver_login_data: DriverLogin, session: AsyncSession = Depends(get_session)
):
    try:
        contact_number = driver_login_data.contact_number
        password = driver_login_data.password

        driver_account = await driver_service.get_driver_by_contact(session, contact_number)
        if driver_account is not None:
            password_valid = verify_password(password, driver_account.password_hash)

            if password_valid:
                access_token = create_access_tokens(
                    user_data={
                        "contact_number": driver_account.contact_number,
                        "driver_id": str(driver_account.driver_id)
                    }
                )

                refresh_token = create_access_tokens(
                    user_data={
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
                        "new_driver": {
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

@driver_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    try:
        expiry_timestamp = token_details['exp']
        if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
            new_access_token = create_access_tokens(user_data=token_details['user'])
            return JSONResponse(content={"access_token": new_access_token})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or Expired Token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@driver_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged out Successfully"},
        status_code=status.HTTP_200_OK,
    )

# --- Driver Profile Management ---
@driver_router.get("/profile")
async def get_driver_profile(current_driver: Driver = Depends(get_current_driver)):
    return current_driver

@driver_router.patch("/profile")
async def update_driver_profile(driver_update: DriverUpdate, current_driver: Driver = Depends(get_current_driver), db: AsyncSession = Depends(get_session)):
    updated_driver = await driver_service.update_driver(db, current_driver.driver_id, driver_update)
    if not updated_driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return updated_driver
