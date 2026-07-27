from fastapi import APIRouter
from shared.utils import success_response

v1_router = APIRouter(prefix="/v1", tags=["Version 1"])

@v1_router.get("/health")
async def health_v1():
    return success_response(
        data={"version": "1.0", "status": "healthy"},
        message="AI Spy Command Center v1 operational"
    )

v2_router = APIRouter(prefix="/v2", tags=["Version 2"])

@v2_router.get("/health")
async def health_v2():
    return success_response(
        data={
            "version": "2.0",
            "status": "healthy",
            "features": ["ai_brain", "websocket_alerts", "cost_optimized_routing"]
        },
        message="AI Spy Command Center v2 operational"
    )