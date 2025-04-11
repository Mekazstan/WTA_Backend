from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from .services import ReportService
from .schemas import OrderReportResponse, RevenueReportResponse, FeedbackReportResponse


report_router = APIRouter()
report_service = ReportService()

# --- Admin Reporting ---
@report_router.get("/orders", response_model=OrderReportResponse)
async def get_orders_report(db: AsyncSession = Depends(get_session)):
    return await report_service.get_order_report(db)

@report_router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report_endpoint(db: AsyncSession = Depends(get_session)):
    return await report_service.get_revenue_report(db)

@report_router.get("/feedback", response_model=FeedbackReportResponse)
async def get_feedback_report_endpoint(db: AsyncSession = Depends(get_session)):
    return await report_service.get_feedback_report(db)