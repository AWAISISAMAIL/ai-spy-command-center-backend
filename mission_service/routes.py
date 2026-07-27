from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from .database import SessionLocal
from . import models, schemas
from auth_service.auth import get_current_user
from auth_service.models import User as AuthUser
from shared.utils import success_response, error_response
import asyncio

router = APIRouter(prefix="/missions", tags=["Missions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mission",
    description="Create a new intelligence mission. Requires authentication. Sends a real-time WebSocket alert to all connected clients.",
    responses={
        201: {"description": "Mission created successfully"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"}
    }
)
def create_mission(
    mission: schemas.MissionCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Create a new mission.
    - **title**: required, 3-100 chars
    - **description**: optional, up to 500 chars
    - **assigned_agent_id**: optional, agent ID from auth service
    """
    new_mission = models.Mission(
        title=mission.title,
        description=mission.description,
        assigned_agent_id=mission.assigned_agent_id
    )
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    mission_data = schemas.MissionResponse.model_validate(new_mission).model_dump()

    # WebSocket broadcast
    from gateway.websocket_manager import manager
    alert = {
        "type": "new_mission",
        "data": {
            "id": mission_data["id"],
            "title": mission_data["title"],
            "status": mission_data["status"],
            "assigned_agent_id": mission_data["assigned_agent_id"]
        }
    }
    async def send_alert():
        await manager.broadcast(alert)
    try:
        asyncio.get_event_loop().run_until_complete(send_alert())
    except:
        pass

    return success_response(
        data=mission_data,
        message="Mission created successfully",
        status_code=status.HTTP_201_CREATED
    )

@router.get(
    "/",
    response_model=None,
    summary="List all missions",
    description="Retrieve a list of missions with optional filtering, sorting, and pagination.",
    responses={
        200: {"description": "List of missions"},
        401: {"description": "Not authenticated"}
    }
)
def list_missions(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(planned|active|completed|failed)$", description="Filter by mission status"),
    agent_id: Optional[int] = Query(None, ge=1, description="Filter by assigned agent ID"),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|title|status)$", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    query = db.query(models.Mission)
    if status_filter:
        query = query.filter(models.Mission.status == status_filter)
    if agent_id:
        query = query.filter(models.Mission.assigned_agent_id == agent_id)
    sort_column = getattr(models.Mission, sort_by, models.Mission.created_at)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    missions = query.offset(skip).limit(limit).all()
    missions_data = [schemas.MissionResponse.model_validate(m).model_dump() for m in missions]
    return success_response(
        data=missions_data,
        message="Missions retrieved successfully"
    )

@router.get(
    "/{mission_id}",
    response_model=None,
    summary="Get a mission by ID",
    description="Retrieve detailed information about a specific mission.",
    responses={
        200: {"description": "Mission details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Mission not found"}
    }
)
def get_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return success_response(
        data=schemas.MissionResponse.model_validate(mission).model_dump(),
        message="Mission retrieved successfully"
    )

@router.patch(
    "/{mission_id}",
    response_model=None,
    summary="Update a mission",
    description="Partially update mission fields (title, description, status, assigned agent).",
    responses={
        200: {"description": "Mission updated"},
        401: {"description": "Not authenticated"},
        404: {"description": "Mission not found"},
        422: {"description": "Validation error"}
    }
)
def update_mission(
    mission_id: int,
    updates: schemas.MissionUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mission, key, value)
    db.commit()
    db.refresh(mission)
    return success_response(
        data=schemas.MissionResponse.model_validate(mission).model_dump(),
        message="Mission updated successfully"
    )

@router.delete(
    "/{mission_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a mission",
    description="Permanently delete a mission. Returns no content on success.",
    responses={
        204: {"description": "Mission deleted"},
        401: {"description": "Not authenticated"},
        404: {"description": "Mission not found"}
    }
)
def delete_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db.delete(mission)
    db.commit()
    return success_response(
        data=None,
        message="Mission deleted successfully",
        status_code=status.HTTP_204_NO_CONTENT
    )