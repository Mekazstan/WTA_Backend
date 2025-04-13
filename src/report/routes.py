from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from db.main import get_session
from .services import ReportService
from .schemas import OrderReportResponse, RevenueReportResponse, FeedbackReportResponse
from auth.dependencies import require_role

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

report_router = APIRouter()
report_service = ReportService()

# --- Admin Reporting ---
@report_router.get("/orders", response_model=OrderReportResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_orders_report(session: AsyncSession = Depends(get_session)):
    try:
        return await report_service.get_order_report(session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_orders_report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the orders report"
        )

@report_router.get("/revenue", response_model=RevenueReportResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_revenue_report_endpoint(session: AsyncSession = Depends(get_session)):
    try:
        return await report_service.get_revenue_report(session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_revenue_report_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the revenue report"
        )

@report_router.get("/feedback", response_model=FeedbackReportResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_feedback_report_endpoint(session: AsyncSession = Depends(get_session)):
    try:
        return await report_service.get_feedback_report(session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_feedback_report_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the feedback report"
        )
        