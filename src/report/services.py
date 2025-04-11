from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy import select
from schemas import OrderReportResponse, RevenueReportResponse, FeedbackReportResponse
from src.db.models import Order, Payment, Feedback


class ReportService:

    async def get_order_report(self, session: AsyncSession) -> OrderReportResponse:
        total_orders_result = await session.execute(select(func.count(Order.order_id)))
        completed_orders_result = await session.execute(select(func.count(Order.order_id)).where(Order.delivery_status == "Delivered"))
        pending_orders_result = await session.execute(select(func.count(Order.order_id)).where(Order.delivery_status == "Pending"))
        return OrderReportResponse(
            total_orders=total_orders_result.scalar_one() or 0,
            completed_orders=completed_orders_result.scalar_one() or 0,
            pending_orders=pending_orders_result.scalar_one() or 0,
        )

    async def get_revenue_report(self, session: AsyncSession) -> RevenueReportResponse:
        paid_orders_result = await session.execute(select(func.sum(Payment.amount)).join(Order).where(Order.payment_status == "Paid"))
        total_revenue = paid_orders_result.scalar_one() or 0.0
        return RevenueReportResponse(total_revenue=total_revenue)

    async def get_feedback_report(self, session: AsyncSession) -> FeedbackReportResponse:
        average_rating_result = await session.execute(select(func.avg(Feedback.rating)))
        feedback_count_result = await session.execute(select(func.count(Feedback.feedback_id)))
        return FeedbackReportResponse(
            average_rating=average_rating_result.scalar_one() or 0.0,
            feedback_count=feedback_count_result.scalar_one() or 0,
        )