from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
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

@driver_router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=DriverResponse)
async def create_driver_account(
    driver_create_data: DriverCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        new_driver = await driver_service.create_driver(session, driver_create_data)
        return new_driver
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact number already exists")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create account")
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
        if driver_account is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Contact Details or Password",
            )

        password_valid = verify_password(password, driver_account.password_hash)
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Contact Details or Password",
            )

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )
    finally:
        await session.close()

@driver_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    try:
        expiry_timestamp = token_details['exp']
        if datetime.fromtimestamp(expiry_timestamp) <= datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Expired refresh token"
            )
            
        new_access_token = create_access_tokens(user_data=token_details['user'])
        return JSONResponse(content={"access_token": new_access_token})
    
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid token format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to refresh token"
        )


@driver_router.get("/logout")
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
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# --- Driver Profile Management ---
@driver_router.get("/profile", response_model=DriverResponse)
async def get_driver_profile(current_driver: Driver = Depends(get_current_driver)):
    try:
        return current_driver
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )

@driver_router.patch("/profile", response_model=DriverResponse)
async def update_driver_profile(
    driver_update: DriverUpdate, 
    current_driver: Driver = Depends(get_current_driver), 
    db: AsyncSession = Depends(get_session)
):
    try:
        updated_driver = await driver_service.update_driver(db, current_driver.driver_id, driver_update)
        if not updated_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Driver not found"
            )
        return updated_driver
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    finally:
        await db.close()
        