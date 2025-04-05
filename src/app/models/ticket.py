from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    status: str = Field(default="open", pattern="^(open|in_progress|resolved|closed)$")

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ai_response: Optional[str] = None
    
    class Config:
        from_attributes = True 