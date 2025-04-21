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
    customer_id: int

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

class OrderUpdate(BaseSchema):
    status: OrderStatus
    driver_id: Optional[int]
    staff_assigned_id: Optional[int]
    driver_charge: Optional[float]