from fastapi import APIRouter, HTTPException, Depends
import pyodbc
import re

from app.models.schemas import TableCreateRequest
from app.core.config import DB_DATABASE_PRACTICE
from app.core.database import build_conn_str

router = APIRouter()

# Dependency to get selected DB name from frontend header
def get_selected_db(x_database_name: str = None):
    return x_database_name or DB_DATABASE_PRACTICE

@router.post("/shops/{shop_name}/create-dynamic-table")
async def create_dynamic_table(
    shop_name: str,
    request: TableCreateRequest,
    db_name: str = Depends(get_selected_db)
):
    # Validate table and column names
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", request.table_name):
        raise HTTPException(400, "Invalid table name")
    for col in request.columns:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col.name):
            raise HTTPException(400, f"Invalid column name: {col.name}")

    # Whitelist allowed types
    allowed_types = {"INT", "VARCHAR", "TEXT", "DATE", "FLOAT", "BOOLEAN"}
    for col in request.columns:
        if col.type.upper().split("(")[0] not in allowed_types:
            raise HTTPException(400, f"Invalid type: {col.type}")

    columns_sql = ", ".join(
        [f"{col.name} {col.type.upper()} {' '.join(col.constraints)}".strip()
         for col in request.columns]
    )
    sql = f"CREATE TABLE {request.table_name} ({columns_sql})"
    try:
        with pyodbc.connect(build_conn_str(db_name)) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        return {"status": "success", "sql": sql}
    except Exception as e:
        raise HTTPException(500, f"Table creation failed: {str(e)}")
