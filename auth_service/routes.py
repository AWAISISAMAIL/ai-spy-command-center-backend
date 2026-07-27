import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from .database import SessionLocal
from . import models, schemas
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from shared.utils import success_response, error_response

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())  # unique token ID
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post(
    "/register",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
    description="Create a new field agent account with a unique username and password. Role defaults to 'agent'.",
    responses={
        201: {"description": "Agent registered successfully"},
        409: {"description": "Username already taken"},
        422: {"description": "Validation error"}
    }
)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    new_user = models.User(
        username=user.username,
        password_hash=hashed.decode('utf-8'),
        role="agent"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user_data = schemas.UserResponse.model_validate(new_user).model_dump()
    return success_response(
        data=user_data,
        message="User registered successfully",
        status_code=status.HTTP_201_CREATED
    )

@router.post(
    "/login",
    response_model=None,
    summary="Login and get JWT tokens",
    description="Authenticate with username and password. Returns access_token (15 min) and refresh_token (7 days). Use refresh token to get new access token without re-login.",
    responses={
        200: {"description": "Login successful, tokens returned"},
        401: {"description": "Invalid username or password"},
        422: {"description": "Validation error"}
    }
)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == login_data.username).first()
    if not user or not bcrypt.checkpw(login_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    access_token = create_access_token({"sub": user.username, "role": user.role})
    refresh_token_str = create_refresh_token(user.id)
    refresh_entry = models.RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_entry)
    db.commit()
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer"
        },
        message="Login successful"
    )

@router.post(
    "/refresh",
    response_model=None,
    summary="Refresh access token",
    description="Provide a valid refresh token to get a new access token + new refresh token. Old refresh token is revoked (rotation).",
    responses={
        200: {"description": "New tokens generated"},
        401: {"description": "Invalid or expired refresh token"},
        422: {"description": "Validation error"}
    }
)
def refresh(refresh_data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    try:
        payload = jwt.decode(refresh_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise credentials_exception
    token_entry = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_data.refresh_token,
        models.RefreshToken.revoked == False,
        models.RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()
    if not token_entry:
        raise credentials_exception
    token_entry.revoked = True
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise credentials_exception
    new_access_token = create_access_token({"sub": user.username, "role": user.role})
    new_refresh_token_str = create_refresh_token(user.id)
    new_refresh_entry = models.RefreshToken(
        token=new_refresh_token_str,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_refresh_entry)
    db.commit()
    return success_response(
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer"
        },
        message="Token refreshed successfully"
    )