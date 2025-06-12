import bcrypt
import jwt
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request, Header, Depends
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse  # HTMLResponse moved here
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal, List
import pyodbc
from fpdf import FPDF
import datetime
from datetime import timedelta, datetime
import os
from enum import Enum
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import re


# Load environment variables
load_dotenv()

SECRET_KEY = "your_super_secret_key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# --- APScheduler background jobs setup ---
scheduler = AsyncIOScheduler()

def backup_job():
    print(f"[{datetime.datetime.now()}] Running DB backup job...")

def daily_report_job():
    print(f"[{datetime.datetime.now()}] Running daily report generation job...")
    today = datetime.date.today()
    condition = f"WHERE CAST(order_date AS DATE) = '{today}'"
    filename = f"auto_report_daily_{today}.pdf"
    query = f"SELECT * FROM orders {condition}"

    with pyodbc.connect(build_conn_str(DB_DATABASE_PRACTICE)) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Smart Ledger Daily Auto Report", ln=True, align="C")
    pdf.set_font("Arial", size=10)

    for row in rows:
        line = ", ".join([f"{col}: {val}" for col, val in zip(headers, row)])
        pdf.multi_cell(0, 8, line)

    report_dir = Path("temp_reports")
    report_dir.mkdir(exist_ok=True)
    path = report_dir / filename
    pdf.output(str(path))

def email_trigger_job():
    print(f"[{datetime.datetime.now()}] Running email trigger job... (Not implemented yet)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(backup_job, CronTrigger(hour=2, minute=0))
    scheduler.add_job(daily_report_job, CronTrigger(hour=3, minute=0))
    scheduler.add_job(email_trigger_job, CronTrigger(hour=4, minute=0))
    scheduler.start()
    print("Scheduler started with 3 daily jobs.")
    yield
    scheduler.shutdown()
    print("Scheduler shut down.")

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="smart-ledger-frontend", html=True), name="static")

@app.get("/")
async def select_db_page():
    return FileResponse(Path("smart-ledger-frontend/select-db.html"))
@app.get("/select-db")
async def select_db_page():
    return FileResponse(Path("smart-ledger-frontend/select-db.html"))

@app.get("/create-db")
async def create_db():
    return FileResponse(Path("smart-ledger-frontend/create-db.html"))

@app.get("/shop/{shop_name}")
async def shop_page(shop_name: str):
    return FileResponse(Path("smart-ledger-frontend/shop/shop.html"))

@app.get("/shop/{shop_name}/dynamic-table")
async def dynamic_table_page(shop_name: str):
    return FileResponse(Path("smart-ledger-frontend/dynamic-table.html"))

@app.get("/login")
async def login_page():
    return FileResponse(Path("smart-ledger-frontend/login.html"))

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return FileResponse("smart-ledger-frontend/select-db.html")

DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE_MASTER = os.getenv("DB_DATABASE_MASTER")
DB_DATABASE_PRACTICE = os.getenv("DB_DATABASE_PRACTICE")

def build_conn_str(db_name: str) -> str:
    return (
        f"Driver={{{DB_DRIVER}}};"
        f"Server={DB_SERVER};"
        f"Database={db_name};"
        "Trusted_Connection=yes;"
    )

# Dependency to get selected DB name from frontend header
def get_selected_db(x_database_name: str = Header(None)):
    return x_database_name or DB_DATABASE_PRACTICE

class ShopCreate(BaseModel):
    name: str
    owner: str

class ColumnDefinition(BaseModel):
    name: str
    type: str
    constraints: List[str] = []

class TableCreateRequest(BaseModel):
    table_name: str
    columns: List[ColumnDefinition]

@app.post("/shops")
async def create_shop(shop: ShopCreate):
    db_name = f"shop_{shop.name.lower().replace(' ', '_')}"
    try:
        with pyodbc.connect(build_conn_str(DB_DATABASE_MASTER), autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create DB: {e}")
    return {"status": "success", "database": db_name}

class TableCreate(BaseModel):
    table_type: Literal["sales", "income", "expense"]

@app.post("/shops/{shop_name}/create-table")
async def create_table(
    shop_name: str,
    payload: TableCreate,
    db_name: str = Depends(get_selected_db)
):
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
            )""",
        "income": """
            CREATE TABLE income (
                id INT PRIMARY KEY IDENTITY(1,1),
                source NVARCHAR(100),
                amount FLOAT,
                received_on DATE DEFAULT GETDATE()
            )""",
        "expense": """
            CREATE TABLE expense (
                id INT PRIMARY KEY IDENTITY(1,1),
                category NVARCHAR(100),
                amount FLOAT,
                spent_on DATE DEFAULT GETDATE(),
                remarks NVARCHAR(255)
            )"""
    }

    if table_type not in table_sql:
        raise HTTPException(status_code=400, detail="Invalid table type.")

    try:
        with pyodbc.connect(build_conn_str(db_name)) as conn:
            cursor = conn.cursor()
            cursor.execute(table_sql[table_type])
            conn.commit()
        return {"status": "success", "table_created": table_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating table: {e}")

@app.post("/shops/{shop_name}/create-dynamic-table")
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
        if col.type.upper() not in allowed_types:
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

@app.post("/shops/{shop_name}/register-admin")
async def register_admin(shop_name: str, user: UserCreate):
    password_hash = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    with pyodbc.connect(build_conn_str(shop_name)) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user.username, password_hash))
        conn.commit()
    return {"status": "admin created"}

@app.post("/login")
async def login(shop_name: str, creds: UserLogin):
    with pyodbc.connect(build_conn_str(shop_name)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (creds.username,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(401, "Invalid username or password")
        password_hash = row[0]
        if not bcrypt.checkpw(creds.password.encode(), password_hash.encode()):
            raise HTTPException(401, "Invalid username or password")
    # Issue JWT
    payload = {
        "shop_name": shop_name,
        "username": creds.username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return {"access_token": token}

def verify_token(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise Exception()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload  # contains shop_name, username, exp
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

@app.get("/protected-resource")
async def protected_route(user=Depends(verify_token)):
    # user["shop_name"], user["username"] available here
    return {"message": "You are authenticated!"}

@app.get("/shops")
async def list_shops():
    try:
        with pyodbc.connect(build_conn_str(DB_DATABASE_MASTER)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE name LIKE 'shop_%'")
            dbs = [row.name for row in cursor.fetchall()]
        return {"shops": dbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching databases: {e}")

@app.post("/select-db")
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

class OrderRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    status: Literal["pending", "completed", "cancelled"]
    order_date: str

@app.post("/add-order")
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

@app.get("/data")
async def get_data(db_name: str = Depends(get_selected_db)):
    with pyodbc.connect(build_conn_str(db_name)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 5 * FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
    return {"data": data}

@app.get("/export-report")
async def export_report(type: Literal["daily", "monthly", "all"] = "daily", db_name: str = Depends(get_selected_db)):
    today = datetime.date.today()
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

@app.get("/summary")
async def get_summary(range: SummaryRange = Query("weekly"), db_name: str = Depends(get_selected_db)):
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=7) if range == "weekly" else today.replace(day=1)
    with pyodbc.connect(build_conn_str(db_name)) as conn:
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
