from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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
    thread_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    
    class Config:
        from_attributes = True 