from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import lifespan
from app.api import routes_auth, routes_shop, routes_dynamic_table, routes_report

app = FastAPI(lifespan=lifespan)

# Serve static frontend
app.mount("/static", StaticFiles(directory="smart-ledger-frontend", html=True), name="static")

# Mount frontend pages
@app.get("/")
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
async def custom_404_handler(_, __):
    return FileResponse("smart-ledger-frontend/select-db.html")

# Include routers
app.include_router(routes_auth.router)
app.include_router(routes_shop.router)
app.include_router(routes_dynamic_table.router)
app.include_router(routes_report.router)
