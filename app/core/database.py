import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine  # for sync MySQL
from typing import Union
from sqlalchemy.orm import declarative_base
Base = declarative_base()

engine_cache = {}
_sessionmakers = {}

def get_engine(shop_id: str) -> Union[create_engine, create_async_engine]:
    if shop_id in engine_cache:
        return engine_cache[shop_id]

    db_url = os.getenv(f"{shop_id.upper()}_DB_URL")
    if not db_url:
        raise ValueError(f"Missing DB URL for shop '{shop_id}'")

    if db_url.startswith("mysql+pymysql://"):
        # Sync engine for MySQL
        engine = create_engine(db_url, future=True)
    elif db_url.startswith("postgresql+asyncpg://"):
        # Async engine for Neon Postgres
        engine = create_async_engine(db_url, future=True, echo=True)
    else:
        raise ValueError(f"Unsupported DB URL scheme for shop '{shop_id}': {db_url}")

    engine_cache[shop_id] = engine
    return engine

def get_session(shop_id: str):
    engine = get_engine(shop_id)
    if shop_id not in _sessionmakers:
        if str(engine.__class__) == "<class 'sqlalchemy.ext.asyncio.engine.AsyncEngine'>":
            _sessionmakers[shop_id] = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        else:
            # sync session for MySQL
            _sessionmakers[shop_id] = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    SessionLocal = _sessionmakers[shop_id]

    # Return async session if async engine, else sync session
    if str(engine.__class__) == "<class 'sqlalchemy.ext.asyncio.engine.AsyncEngine'>":
        return SessionLocal()
    else:
        return SessionLocal()
