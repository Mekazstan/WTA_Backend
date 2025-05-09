from datetime import datetime
from pydantic import BaseModel, EmailStr

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        
class CustomerBase(BaseSchema):
    first_name: str
    last_name: str
    email: EmailStr

class CustomerCreate(CustomerBase):
    password: str

class CustomerRead(CustomerBase):
    id: int
    registration_date: datetime