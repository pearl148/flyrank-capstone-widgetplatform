from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import User, Tenant
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))



router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"],deprecated= "auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)

class LoginResponse(BaseModel):
    access_token : str
    token_type : str = "bearer"

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == credentials.email)).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id})
    return LoginResponse(access_token=access_token)


class SignUpRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)

class SignUpResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/signup",response_model=SignUpResponse)
def signup(data:SignUpRequest, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == data.email)).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    new_tenant = Tenant(name=data.company_name)
    session.add(new_tenant)
    session.flush()
    new_user = User(tenant_id=new_tenant.id, email=data.email, password_hash=hash_password(data.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    access_token = create_access_token(data={"sub": new_user.email, "user_id":new_user.id, "tenant_id": new_tenant.id})
    return SignUpResponse(access_token=access_token)


# It is to get the current user from the token
bearer_scheme = HTTPBearer()
def get_current_user(
        creds:HTTPAuthorizationCredentials = Depends(bearer_scheme),
        session: Session = Depends(get_session),
) ->User:
    payload = decode_access_token(creds.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = session.exec(select(User).where(User.id == payload.get("user_id"))).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user