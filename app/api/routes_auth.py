from fastapi import APIRouter, HTTPException, Header, Depends
from datetime import datetime, timedelta
import pyodbc
import bcrypt
import jwt
from app.core.config import (
    SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES,
    DB_DRIVER, DB_SERVER, DB_DATABASE_MASTER
)
from app.models.schemas import UserCreate, UserLogin

router = APIRouter()

def build_conn_str(db_name: str) -> str:
    return (
        f"Driver={{{DB_DRIVER}}};"
        f"Server={DB_SERVER};"
        f"Database={db_name};"
        "Trusted_Connection=yes;"
    )

@router.post("/register-shop")
async def register_shop(user: UserCreate):
    shop_name = user.username.lower().replace(" ", "_")
    db_name = f"shop_{shop_name}"

    # Step 1: Create the shop database
    try:
        with pyodbc.connect(build_conn_str(DB_DATABASE_MASTER), autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create DB: {e}")

    # Step 2: Create users table if not exists, and add admin user
    password_hash = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    try:
        with pyodbc.connect(build_conn_str(db_name)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT * FROM sysobjects 
                    WHERE name='users' AND xtype='U'
                )
                CREATE TABLE users (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    username NVARCHAR(100) UNIQUE NOT NULL,
                    password_hash NVARCHAR(255) NOT NULL
                )
            """)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (user.username, password_hash)
            )
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating admin user: {e}")

    # Step 3: Return token
    payload = {
        "shop_name": db_name,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return {
        "status": "shop created",
        "database": db_name,
        "access_token": token
    }

@router.post("/login")
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
        return payload
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

@router.get("/protected-resource")
async def protected_route(user=Depends(verify_token)):
    return {"message": "You are authenticated!"}
