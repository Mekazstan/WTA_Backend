from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from order.schemas import OrderResponse

class CustomerBase(BaseModel):
    email: str = Field(..., example="customer@example.com")
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    address: Optional[str] = Field(None, example="123 Main St")
    contact_number: Optional[str] = Field(None, example="+1234567890")
    
    class Config:
        from_attributes = True

class CustomerCreate(CustomerBase):
    password: Optional[str] = Field(None, min_length=6, example="newpassword")
    
    class Config:
        from_attributes = True

class CustomerUpdate(CustomerBase):
    email: Optional[str] = Field(None, example="new.email@example.com")
    password: Optional[str] = Field(None, min_length=6, example="newpassword")
    
    class Config:
        from_attributes = True

class CustomerResponse(CustomerBase):
    customer_id: UUID
    registration_date: datetime

    class Config:
        from_attributes = True

class CustomerLogin(BaseModel):
    email: str = Field(..., example="customer@example.com")
    password: str = Field(..., example="securepassword")
    
    class Config:
        from_attributes = True
    
    