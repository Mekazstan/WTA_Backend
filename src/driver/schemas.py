from datetime import datetime
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