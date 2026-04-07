from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
import httpx
import uuid
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

# Synthetic agent endpoint : bypasses OAuth, used for testing only
@router.post("/auth/token")
async def login(user_id: str | None = None):
    if not user_id:
        user_id = str(uuid.uuid4())
    token = create_access_token(data={"sub": user_id})
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Google OAuth endpoint
class GoogleTokenRequest(BaseModel):
    token: str

@router.post("/auth/google")
async def login_with_google(body: GoogleTokenRequest):
    """
    Verifies a Google token (ID token from web app or access token from Chrome
    extension), extracts the user's Google ID (sub), email, and display name,
    then issues our own signed JWT with the Google ID as the sub claim.
    """
    google_id = None
    email = ""
    name = ""

    async with httpx.AsyncClient() as client:
        # First try as an ID token
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": body.token}
        )
        if resp.status_code == 200:
            info = resp.json()
            # Validate the token was issued for our app
            if GOOGLE_CLIENT_ID and info.get("aud") != GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token audience mismatch"
                )
            google_id = info.get("sub")
            email = info.get("email", "")
            name = info.get("name", "")
        else:
            # Fall back to treating it as an OAuth access token
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {body.token}"}
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Google token"
                )
            info = resp.json()
            google_id = info.get("sub")
            email = info.get("email", "")
            name = info.get("name", "")

    if not google_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not extract Google ID from token"
        )

    # Using first part of email as fallback display name
    if not name:
        name = email.split("@")[0]

    # Upsert the user in Neo4j so their Google ID exists as a User node
    try:
        from neo4j_client import upsert_user
        upsert_user(google_id, email, name)
    except Exception:
        pass

    # Issue our JWT with Google ID as the sub claim
    access_token = create_access_token(data={"sub": google_id, "email": email, "name": name})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": google_id,
        "name": name,
        "email": email,
    }