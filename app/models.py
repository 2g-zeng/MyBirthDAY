# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class VideoJob(Base):
    """
    Represents a video generation job.
    One job may contain multiple uploaded images and one text content.
    For MVP, we store only the video path and text; image paths can be
    handled by a simple naming convention or extended later.
    """
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    text_content = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    video_path = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
