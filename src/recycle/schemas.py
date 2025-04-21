from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from src.customer.schemas import CustomerRead
from src.db.models import RecyclableStatus, PickupOption

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

class RecyclableSubmissionBase(BaseSchema):
    recyclable_type: str
    pickup_option: PickupOption
    pickup_address: Optional[str]
    dropoff_location: Optional[str]
    status: RecyclableStatus = RecyclableStatus.PENDING_REVIEW

class RecyclableSubmissionCreate(RecyclableSubmissionBase):
    customer_id: int
    image_url: str

class RecyclableSubmissionRead(RecyclableSubmissionBase):
    id: int
    customer: CustomerRead
    submission_date: datetime
    estimated_value: Optional[float]
    credited_amount: Optional[float]

class RecyclableSubmissionUpdate(BaseSchema):
    status: RecyclableStatus
    estimated_value: Optional[float]
    credited_amount: Optional[float]
