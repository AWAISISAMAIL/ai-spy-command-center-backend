from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MissionCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, example="Operation Shadow Strike")
    description: Optional[str] = Field(None, max_length=500, example="Infiltrate enemy base")
    assigned_agent_id: Optional[int] = Field(None, ge=1, example=1)

class MissionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(planned|active|completed|failed)$")
    assigned_agent_id: Optional[int] = Field(None, ge=1)

class MissionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    assigned_agent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True