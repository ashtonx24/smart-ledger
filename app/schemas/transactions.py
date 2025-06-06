from pydantic import BaseModel
from datetime import date
from typing import Optional
from enum import Enum

class TransactionType(str, Enum):
    credit = "credit"
    debit = "debit"

class TransactionCreate(BaseModel):
    date: date
    item_name: str
    company: Optional[str] = None
    amount: float
    type: TransactionType
    notes: Optional[str] = None

class TransactionOut(TransactionCreate):
    id: int

    model_config = {
        "from_attributes": True  # <--- new way in Pydantic v2
    }
