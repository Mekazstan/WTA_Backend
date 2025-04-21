from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

class DriverBase(BaseSchema):
    first_name: str
    last_name: str
    phone_number: str
    vehicle_details: str
    is_active: bool

class DriverCreate(DriverBase):
    pass

class DriverRead(DriverBase):
    id: int
    created_at: datetime
    
class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    vehicle_details: Optional[str] = None
    is_active: Optional[bool] = None