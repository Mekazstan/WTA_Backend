from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class OrderBase(BaseModel):
    quantity: float = Field(..., example=5000.0)
    location_address: str
    delivery_schedule: datetime = Field(..., example="2025-04-15T10:00:00")
    payment_method: Optional[str] = Field(None, example="Card")
    
    class Config:
        from_attributes = True

class OrderCreate(OrderBase):
    customer_id: UUID
    
    class Config:
        from_attributes = True

class OrderUpdate(OrderBase):
    quantity: Optional[float] = Field(None, example=6000.0)
    delivery_status: Optional[str] = Field(None, example="On the way", description="Pending, Assigned, On the way, Delivered, Cancelled")
    assigned_driver_id: Optional[UUID] = Field(None, example="some-driver-uuid")
    payment_status: Optional[str] = Field(None, example="Paid", description="Pending, Paid, Failed")
    cancellation_reason: Optional[str] = None

    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    order_id: UUID
    customer_id: UUID
    order_date: datetime
    delivery_status: str
    assigned_driver_id: Optional[UUID]
    payment_status: Optional[str]
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderAssign(BaseModel):
    driver_id: UUID = Field(..., example="some-driver-uuid")
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    delivery_status: str = Field(..., example="Delivered", description="Pending, Assigned, On the way, Delivered, Cancelled")
    
    class Config:
        from_attributes = True

class OrderCancellationRequest(BaseModel):
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True