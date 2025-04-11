from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import FeedbackCreate
from db.models import Feedback

class FeedbackService:
    async def create_feedback(self, session: AsyncSession, feedback: FeedbackCreate) -> Feedback:
        db_feedback = Feedback(**feedback.dict())
        session.add(db_feedback)
        await session.commit()
        await session.refresh(db_feedback)
        return db_feedback