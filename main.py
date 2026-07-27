import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from auth_service.database import engine as auth_engine, Base as AuthBase
from mission_service.database import engine as mission_engine, Base as MissionBase
from intel_service.database import engine as intel_engine, Base as IntelBase
from auth_service import models as auth_models
from mission_service import models as mission_models
from intel_service import models as intel_models
from auth_service.routes import router as auth_router
from mission_service.routes import router as mission_router
from intel_service.routes import router as intel_router
from ai_brain_service.routes import router as ai_brain_router
from auth_service.auth import get_current_user
from gateway.middleware import setup_gateway
from shared.utils import success_response, error_response
from api_versions import v1_router, v2_router
from gateway.websocket_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    AuthBase.metadata.create_all(bind=auth_engine)
    MissionBase.metadata.create_all(bind=mission_engine)
    IntelBase.metadata.create_all(bind=intel_engine)
    yield

app = FastAPI(
    title="AI Spy Command Center",
    version="1.0.0",
    description="Intelligence operations platform – Mission Control API",
    lifespan=lifespan
)

setup_gateway(app)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(
        message=exc.detail,
        status_code=exc.status_code,
        error_code="HTTP_ERROR"
    )

app.include_router(auth_router)
app.include_router(mission_router)
app.include_router(intel_router)
app.include_router(ai_brain_router)
app.include_router(v1_router)
app.include_router(v2_router)

@app.get("/")
async def root():
    return success_response(
        data={"service": "AI Spy Command Center", "status": "operational"},
        message="Welcome to Mission Control"
    )

@app.get("/test-protected")
async def test_protected(current_user=Depends(get_current_user)):
    return success_response(
        data={"username": current_user.username, "role": current_user.role},
        message="Authenticated user info"
    )

# Emergency endpoint to create tables if not created automatically
@app.get("/init-db")
async def init_database():
    try:
        AuthBase.metadata.create_all(bind=auth_engine)
        MissionBase.metadata.create_all(bind=mission_engine)
        IntelBase.metadata.create_all(bind=intel_engine)
        return {"message": "All tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)