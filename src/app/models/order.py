from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

class OrderItem(BaseModel):
    productId: str
    quantity: int
    price: Decimal

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    userEmail: str
    items: List[OrderItem]
    total: Decimal
    status: str = Field(default="Pending", pattern="^(Pending|Completed|Canceled)$")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True 