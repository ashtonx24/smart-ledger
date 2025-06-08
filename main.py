from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import pyodbc
from fastapi import Request

app = FastAPI()

# Serve static assets
app.mount("/static", StaticFiles(directory="smart-ledger-frontend", html=True), name="static")

# Serve index.html directly at root
@app.get("/")
async def root():
    return FileResponse(Path("smart-ledger-frontend/index.html"))

# Your DB connection and route (ensure it's still correct)
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
        cursor.execute("SELECT TOP 5 * FROM orders")
        rows = cursor.fetchall()
        return {"data": [dict(zip([column[0] for column in cursor.description], row)) for row in rows]}

@app.post("/add-order")
async def add_order(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    amount = data.get("amount")
    status = data.get("status")
    order_date = data.get("order_date")

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
            (user_id, amount, status, order_date)
        )
        conn.commit()
    return {"status": "success"}
