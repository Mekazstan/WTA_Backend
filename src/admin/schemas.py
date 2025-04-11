from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class AdminUserBase(BaseModel):
    username: str = Field(..., example="adminuser")
    email: str = Field(..., example="admin@example.com")
    password: str = Field(..., min_length=6, example="adminpassword")
    
    class Config:
        from_attributes = True

class AdminUserCreate(AdminUserBase):
    pass

class AdminUserLogin(AdminUserBase):
    pass

