from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import pyodbc
from app.models.schemas import ShopCreate
from app.core.config import DB_DATABASE_MASTER
from app.core.database import build_conn_str

router = APIRouter()

@router.post("/shops")
async def create_shop(shop: ShopCreate):
    db_name = f"shop_{shop.name.lower().replace(' ', '_')}"
    try:
        with pyodbc.connect(build_conn_str(DB_DATABASE_MASTER), autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create DB: {e}")
    return {"status": "success", "database": db_name}

@router.get("/shops")
async def list_shops():
    try:
        with pyodbc.connect(build_conn_str(DB_DATABASE_MASTER)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE name LIKE 'shop_%'")
            dbs = [row.name for row in cursor.fetchall()]
        return {"shops": dbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching databases: {e}")

@router.post("/select-db")
async def select_db(request: Request):
    data = await request.json()
    db_name = data.get("db_name")
    if not db_name:
        raise HTTPException(status_code=400, detail="No database name provided.")
    try:
        with pyodbc.connect(build_conn_str(DB_DATABASE_MASTER)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE name = ?", (db_name,))
            exists = cursor.fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Database not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating database: {e}")
    return JSONResponse(content={"status": "selected", "database": db_name})
