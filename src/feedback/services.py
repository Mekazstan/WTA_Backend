from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import FeedbackCreate
from db.models import Feedback

class FeedbackService:
    async def create_feedback(self, session: AsyncSession, feedback: FeedbackCreate) -> Feedback:
        try:
            db_feedback = Feedback(**feedback.dict())
            session.add(db_feedback)
            await session.commit()
            await session.refresh(db_feedback)
            return db_feedback
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
            