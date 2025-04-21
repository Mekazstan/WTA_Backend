from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from db.models import OrderStatus, PaymentStatus
from customer.schemas import CustomerRead

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        
class OrderBase(BaseSchema):
    destination_address: str
    water_amount: float
    status: OrderStatus = OrderStatus.PAIRING

class OrderCreate(OrderBase):
    pass

class OrderRead(OrderBase):
    id: int
    customer: CustomerRead
    created_at: datetime
    updated_at: datetime
    driver_id: Optional[int]
    staff_assigned_id: Optional[int]
    driver_charge: Optional[float]
    payment_status: PaymentStatus
    payment_date: Optional[datetime]

class OrderUpdate(BaseModel):
    destination_address: Optional[str] = None
    water_amount: Optional[float] = None
    status: Optional[OrderStatus] = None
    driver_id: Optional[int] = None
    driver_charge: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None
    payment_date: Optional[datetime] = None