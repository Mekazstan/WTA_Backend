from pydantic import BaseModel

class OrderReportResponse(BaseModel):
    total_orders: int
    completed_orders: int
    pending_orders: int
    
    class Config:
        from_attributes = True

class RevenueReportResponse(BaseModel):
    total_revenue: float
    
    class Config:
        from_attributes = True

class FeedbackReportResponse(BaseModel):
    average_rating: float
    feedback_count: int
    
    class Config:
        from_attributes = True