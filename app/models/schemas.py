from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum

# ---------- User & Auth ----------
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# ---------- Shops ----------
class ShopCreate(BaseModel):
    name: str
    owner: str

# ---------- Tables ----------
class TableCreate(BaseModel):
    table_type: Literal["sales", "income", "expense"]

class ColumnDefinition(BaseModel):
    name: str
    type: str
    constraints: List[str] = []

class TableCreateRequest(BaseModel):
    table_name: str
    columns: List[ColumnDefinition]

# ---------- Orders ----------
class OrderRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    status: Literal["pending", "completed", "cancelled"]
    order_date: str

# ---------- Summary ----------
class SummaryRange(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
