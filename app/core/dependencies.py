from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session

def get_shop_id(x_shop_id: str = Header(...)):
    if not x_shop_id:
        raise HTTPException(status_code=400, detail="Missing X-Shop-Id header")
    return x_shop_id

# Async dependency for Neon Postgres shops
async def get_db_async(shop_id: str = Depends(get_shop_id)) -> AsyncSession:
    session = get_session(shop_id)
    if not isinstance(session, AsyncSession):
        raise HTTPException(status_code=400, detail="Expected async session but got sync")
    async with session as s:
        yield s
