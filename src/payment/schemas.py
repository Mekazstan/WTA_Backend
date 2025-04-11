from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class PaymentBase(BaseModel):
    order_id: UUID
    amount: float = Field(..., example=50.00)
    transaction_id: Optional[str] = Field(None, example="txn_12345")
    status: Optional[str] = Field("Pending", example="Success", description="Success, Failed, Pending")

    class Config:
        from_attributes = True


class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    payment_id: UUID
    payment_date: datetime

    class Config:
        from_attributes = True
        