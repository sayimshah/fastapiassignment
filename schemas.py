from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import Optional

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    item_name: str
    quantity: int = Field(..., ge=0)
    expiry_date: date

class ItemResponse(ItemCreate):
    id: str
    insert_date: datetime

class ClockInCreate(BaseModel):
    email: EmailStr
    location: str

class ClockInResponse(ClockInCreate):
    id: str
    insert_datetime: datetime
