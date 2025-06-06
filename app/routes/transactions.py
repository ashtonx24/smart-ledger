from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db_async
from app.crud import transactions as crud
from app.schemas import transactions as schemas
from typing import List

router = APIRouter()

@router.post("/", response_model=schemas.TransactionOut)
async def add_transaction(data: schemas.TransactionCreate, db: AsyncSession = Depends(get_db_async)):
    return await crud.create_transaction(db, data.dict())

@router.get("/", response_model=List[schemas.TransactionOut])
async def fetch_all(db: AsyncSession = Depends(get_db_async)):
    return await crud.get_all_transactions(db)
