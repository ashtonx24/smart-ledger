from fastapi import FastAPI
from app.routes import transactions
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
@app.get("/")
def root():
    return {"message": "Smart Ledger API is alive and kicking 🚀"}
