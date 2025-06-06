from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transaction import Transaction

async def create_transaction(db: AsyncSession, data: dict):
    txn = Transaction(**data)
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn

async def get_all_transactions(db: AsyncSession):
    result = await db.execute(select(Transaction).order_by(Transaction.id.desc()))
    return result.scalars().all()
