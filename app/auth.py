import os, time, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ALGORITHM = os.getenv("JWT_ALG","HS256")
SECRET = os.getenv("JWT_SECRET","change-me-in-prod")
security = HTTPBearer()

def create_token(sub: str) -> str:
    # 'Indefinite' per spec: no exp claim, but include iat
    payload = {"sub": sub, "iat": int(time.time())}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM], options={"verify_exp": False})
        return payload.get("sub") or "unknown"
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
