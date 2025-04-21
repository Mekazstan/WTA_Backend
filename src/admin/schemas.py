from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

class SuperAdminBase(BaseSchema):
    email: EmailStr

class SuperAdminCreate(SuperAdminBase):
    password: str

class SuperAdminRead(SuperAdminBase):
    id: int
    created_at: datetime

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class StaffUpdate(BaseSchema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None