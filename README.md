# Smart Ledger

## Setup

1. Create and activate Python virtual environment  
2. Install dependencies: `pip install fastapi uvicorn pyodbc`

3. Ensure SQL Server Express is running and DB + `orders` table exist

4. Run app: `uvicorn main:app --reload`

5. Access frontend at `http://localhost:8000/`

## DB connection

Update connection string in `main.py` if needed.

## Future work

- Add validation & error handling
- Add authentication
- Add summary reports, PDF export
- Switch to PostgreSQL (planned)
