# SQLAlchemy models
from sqlalchemy import Column, Integer, String, Float, Text, Enum
from app.core.database import Base
import enum

class TransactionType(enum.Enum):
    credit = "credit"
    debit = "debit"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(20), nullable=False)
    item_name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    notes = Column(Text, nullable=True)
