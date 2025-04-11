from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class FeedbackBase(BaseModel):
    order_id: UUID
    customer_id: UUID
    rating: int = Field(..., ge=1, le=5, example=4)
    comment: Optional[str] = Field(None, example="Good service!")
    
    class Config:
        from_attributes = True

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackResponse(FeedbackBase):
    feedback_id: UUID
    feedback_date: datetime

    class Config:
        from_attributes = True