from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class DriverBase(BaseModel):
    name: str = Field(..., example="Tanker Driver 1")
    contact_number: str = Field(..., example="+9876543210")
    vehicle_details: Optional[str] = Field(None, example="Truck Model XYZ")
    verification_status: Optional[str] = Field("Pending", example="Verified")
    
    class Config:
        from_attributes = True

class DriverCreate(DriverBase):
    password: str = Field(..., min_length=6, example="driverpassword")
    
    class Config:
        from_attributes = True

class DriverLogin(BaseModel):
    contact_number: str = Field(..., example="+9876543210")
    password: str = Field(..., example="driverpassword")
    
    class Config:
        from_attributes = True

class DriverUpdate(DriverBase):
    name: Optional[str] = Field(None, example="Updated Driver Name")
    contact_number: Optional[str] = Field(None, example="+1122334455")
    
    class Config:
        from_attributes = True

class DriverResponse(DriverBase):
    driver_id: UUID
    registration_date: datetime
    is_active: bool

    class Config:
        from_attributes = True