from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import schemas, services, models
from database import get_db
from .utils import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

driver_router = APIRouter()

# --- Utility Functions for Drivers ---
async def get_current_driver(db: AsyncSession = Depends(get_db), token: str = Depends(OAuth2PasswordRequestForm)):
    """Placeholder for driver authentication."""
    driver = await services.get_driver_by_contact(db, token.username)
    if not driver or not verify_password(token.password, "placeholder_password"):  # Replace with actual password storage for drivers
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return driver

# --- Driver Authentication ---
@driver_router.post("/register", response_model=schemas.DriverResponse, status_code=status.HTTP_201_CREATED)
async def register_driver(driver: schemas.DriverCreate, db: AsyncSession = Depends(get_db)):
    db_driver = await services.get_driver_by_contact(db, driver.contact_number)
    if db_driver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver with this contact number already exists")
    return await services.create_driver(db, driver)

@driver_router.post("/login", response_model=schemas.TokenResponse)
async def login_driver(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Placeholder for driver login. In a real scenario, you'd authenticate against stored credentials."""
    driver = await services.get_driver_by_contact(db, form_data.username)
    # In a real scenario, you would retrieve the driver's hashed password and verify it.
    # For this MVP, assuming a placeholder or no direct login for drivers.
    if not driver:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid contact number")
    # Since drivers in the MVP don't have direct login, we'll just create a token based on their contact.
    # In a future version with a driver app, this would involve password verification.
    access_token_expires = timedelta(minutes=30) # Adjust as needed
    access_token = create_access_token(data={"sub": driver.contact_number, "role": "driver"}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# --- Driver Profile Management ---
@driver_router.get("/profile", response_model=schemas.DriverResponse)
async def get_driver_profile(current_driver: models.Driver = Depends(get_current_driver)):
    return current_driver

@driver_router.put("/profile", response_model=schemas.DriverResponse)
async def update_driver_profile(driver_update: schemas.DriverUpdate, current_driver: models.Driver = Depends(get_current_driver), db: AsyncSession = Depends(get_db)):
    updated_driver = await services.update_driver(db, current_driver.driver_id, driver_update)
    if not updated_driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return updated_driver
