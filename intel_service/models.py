from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from datetime import datetime, timezone
from .database import Base

class IntelReport(Base):
    __tablename__ = "intel_reports"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, nullable=False)  # reference to mission_service mission id
    agent_id = Column(Integer, nullable=False)    # reference to auth_service user id
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)         # AI-generated summary (baad mein fill hoga)
    ai_model_used = Column(String, nullable=True)  # e.g., "gemini-flash", "gpt-4"
    cost = Column(Float, default=0.0)             # AI call cost in USD
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))