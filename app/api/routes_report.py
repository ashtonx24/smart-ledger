from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from fpdf import FPDF
import pyodbc

from app.models.schemas import OrderRequest
from app.core.config import DB_DATABASE_PRACTICE
from app.core.database import build_conn_str

router = APIRouter()

# Dependency to get selected DB name
def get_selected_db(x_database_name: str = None):
    return x_database_name or DB_DATABASE_PRACTICE

@router.post("/add-order")
async def add_order(data: OrderRequest, db_name: str = Depends(get_selected_db)):
    try:
        with pyodbc.connect(build_conn_str(db_name)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, amount, status, order_date) VALUES (?, ?, ?, ?)",
                (data.user_id, data.amount, data.status, data.order_date)
            )
            conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data")
async def get_data(db_name: str = Depends(get_selected_db)):
    with pyodbc.connect(build_conn_str(db_name)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 5 * FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
    return {"data": data}

@router.get("/export-report")
async def export_report(type: str = "daily", db_name: str = Depends(get_selected_db)):
    today = date.today()
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

    with pyodbc.connect(build_conn_str(db_name)) as conn:
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

    report_dir = Path("temp_reports")
    report_dir.mkdir(exist_ok=True)
    path = report_dir / filename
    pdf.output(str(path))
    return FileResponse(path, filename=filename, media_type="application/pdf")

class SummaryRange(str, Enum):
    weekly = "weekly"
    monthly = "monthly"

@router.get("/summary")
async def get_summary(range: SummaryRange = Query("weekly"), db_name: str = Depends(get_selected_db)):
    today = date.today()
    from_date = today - timedelta(days=7) if range == "weekly" else today.replace(day=1)

    with pyodbc.connect(build_conn_str(db_name)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(amount) as total_income,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
            FROM orders
            WHERE order_date >= ?
        """, (from_date,))
        row = cursor.fetchone()

    return {
        "range": range,
        "from_date": str(from_date),
        "to_date": str(today),
        "total_orders": row.total_orders or 0,
        "total_income": float(row.total_income or 0),
        "completed_orders": row.completed_orders or 0
    }
