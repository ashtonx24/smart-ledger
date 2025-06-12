import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from pathlib import Path
from fpdf import FPDF
import pyodbc
import datetime

# Load from .env
load_dotenv()

DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE_MASTER = os.getenv("DB_DATABASE_MASTER")
DB_DATABASE_PRACTICE = os.getenv("DB_DATABASE_PRACTICE")
SECRET_KEY = "your_super_secret_key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30

# APScheduler
scheduler = AsyncIOScheduler()

def build_conn_str(db_name: str) -> str:
    return (
        f"Driver={{{DB_DRIVER}}};"
        f"Server={DB_SERVER};"
        f"Database={db_name};"
        "Trusted_Connection=yes;"
    )

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
async def lifespan(app):
    scheduler.add_job(backup_job, CronTrigger(hour=2, minute=0))
    scheduler.add_job(daily_report_job, CronTrigger(hour=3, minute=0))
    scheduler.add_job(email_trigger_job, CronTrigger(hour=4, minute=0))
    scheduler.start()
    print("Scheduler started with 3 daily jobs.")
    yield
    scheduler.shutdown()
    print("Scheduler shut down.")
