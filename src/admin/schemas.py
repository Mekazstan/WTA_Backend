from datetime import datetime
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

