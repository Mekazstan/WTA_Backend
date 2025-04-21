from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        
class StaffBase(BaseSchema):
    first_name: str
    last_name: str
    email: EmailStr

class StaffCreate(StaffBase):
    password: str
    created_by_id: Optional[int]

class StaffRead(StaffBase):
    id: int
    created_at: datetime
    created_by_id: Optional[int]