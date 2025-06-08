from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal
import pyodbc
from fpdf import FPDF
import datetime
import os
from enum import Enum

app = FastAPI()

# Serve static frontend assets
app.mount("/static", StaticFiles(directory="smart-ledger-frontend", html=True), name="static")

# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse(Path("smart-ledger-frontend/index.html"))

# Master DB connection
conn_str_master = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DESKTOP-DK5PTGB\\SQLEXPRESS;"
    "Database=master;"
    "Trusted_Connection=yes;"
)

# Template for shop DBs
conn_str_shop_template = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DESKTOP-DK5PTGB\\SQLEXPRESS;"
    "Database={db_name};"
    "Trusted_Connection=yes;"
)

# 📦 Shop creation model
class ShopCreate(BaseModel):
    name: str
    owner: str

@app.post("/shops")
async def create_shop(shop: ShopCreate):
    db_name = f"shop_{shop.name.lower().replace(' ', '_')}"
    try:
        with pyodbc.connect(conn_str_master) as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create DB: {e}")
    return {"status": "success", "database": db_name}

# 📥 Create tables per shop
class TableCreate(BaseModel):
    table_type: Literal["sales", "income", "expense"]

@app.post("/shops/{shop_name}/create-table")
async def create_table(shop_name: str, payload: TableCreate):
    db_name = f"shop_{shop_name.lower().replace(' ', '_')}"
    table_type = payload.table_type.lower()

    table_sql = {
        "sales": """
            CREATE TABLE sales (
                id INT PRIMARY KEY IDENTITY(1,1),
                item_name NVARCHAR(100),
                quantity INT,
                price FLOAT,
                total FLOAT,
                sale_date DATE DEFAULT GETDATE()
            )
        """,
        "income": """
            CREATE TABLE income (
                id INT PRIMARY KEY IDENTITY(1,1),
                source NVARCHAR(100),
                amount FLOAT,
                received_on DATE DEFAULT GETDATE()
            )
        """,
        "expense": """
            CREATE TABLE expense (
                id INT PRIMARY KEY IDENTITY(1,1),
                category NVARCHAR(100),
                amount FLOAT,
                spent_on DATE DEFAULT GETDATE(),
                remarks NVARCHAR(255)
            )
        """
    }

    if table_type not in table_sql:
        raise HTTPException(status_code=400, detail="Invalid table type.")

    try:
        conn_str = conn_str_shop_template.format(db_name=db_name)
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(table_sql[table_type])
            conn.commit()
        return {"status": "success", "table_created": table_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating table: {e}")

# 🧾 Order model with validation
class OrderRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    status: Literal["pending", "completed", "cancelled"]
    order_date: str  # ISO format: YYYY-MM-DD

@app.post("/add-order")
async def add_order(data: OrderRequest):
    try:
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=DESKTOP-DK5PTGB\\SQLEXPRESS;"
            "Database=Practice;"
            "Trusted_Connection=yes;"
        )
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, amount, status, order_date) VALUES (?, ?, ?, ?)",
                (data.user_id, data.amount, data.status, data.order_date)
            )
            conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data")
async def get_data():
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-DK5PTGB\\SQLEXPRESS;"
        "Database=Practice;"
        "Trusted_Connection=yes;"
    )
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 5 * FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
    return {"data": data}

# 📤 PDF Export Endpoint
@app.get("/export-report")
async def export_report(type: Literal["daily", "monthly", "all"] = "daily"):
    today = datetime.date.today()
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-DK5PTGB\\SQLEXPRESS;"
        "Database=Practice;"
        "Trusted_Connection=yes;"
    )

    if type == "daily":
        condition = f"WHERE CAST(order_date AS DATE) = '{today}'"
        filename = f"report_daily_{today}.pdf"
    elif type == "monthly":
        first_day = today.replace(day=1)
        condition = f"WHERE order_date >= '{first_day}'"
        filename = f"report_monthly_{today.strftime('%Y-%m')}.pdf"
    else:
        condition = ""
        filename = f"report_all_{today}.pdf"

    query = f"SELECT * FROM orders {condition}"

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Smart Ledger Report", ln=True, align="C")
    pdf.set_font("Arial", size=10)

    for row in rows:
        line = ", ".join([f"{col}: {val}" for col, val in zip(headers, row)])
        pdf.multi_cell(0, 8, line)

    # Save and return file
    report_dir = Path("temp_reports")
    report_dir.mkdir(exist_ok=True)
    path = report_dir / filename
    pdf.output(str(path))

    return FileResponse(path, filename=filename, media_type="application/pdf")

# 📊 Summary Endpoint
class SummaryRange(str, Enum):
    weekly = "weekly"
    monthly = "monthly"

@app.get("/summary")
async def get_summary(range: SummaryRange = Query("weekly")):
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=7) if range == "weekly" else today.replace(day=1)

    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-DK5PTGB\\SQLEXPRESS;"
        "Database=Practice;"
        "Trusted_Connection=yes;"
    )
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_orders,
                SUM(amount) as total_income,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
            FROM orders
            WHERE order_date >= ?
            """,
            (from_date,)
        )
        row = cursor.fetchone()

    return {
        "range": range,
        "from_date": str(from_date),
        "to_date": str(today),
        "total_orders": row.total_orders or 0,
        "total_income": float(row.total_income or 0),
        "completed_orders": row.completed_orders or 0
    }
