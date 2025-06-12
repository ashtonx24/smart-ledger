from fastapi import Header, HTTPException
import jwt
from app.core.config import SECRET_KEY, JWT_ALGORITHM

def verify_token(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload  # contains shop_name, username, exp
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
