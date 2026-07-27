from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class IntelReportCreate(BaseModel):
    mission_id: int = Field(..., ge=1, example=1)
    raw_text: str = Field(..., min_length=10, max_length=2000, example="Enemy spotted near sector 7. Coordinates 34.05N, 71.12E.")

class IntelReportResponse(BaseModel):
    id: int
    mission_id: int
    agent_id: int
    raw_text: str
    summary: Optional[str] = None
    ai_model_used: Optional[str] = None
    cost: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True