from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from .database import SessionLocal
from . import models, schemas
from auth_service.auth import get_current_user
from auth_service.models import User as AuthUser
from shared.utils import success_response, error_response

router = APIRouter(prefix="/intel", tags=["Intel Reports"])

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
    summary="Submit a field intel report",
    description="Agents submit raw intelligence from the field. Report is stored and can later be summarized by AI Brain.",
    responses={
        201: {"description": "Intel report submitted successfully"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"}
    }
)
def submit_intel(
    intel: schemas.IntelReportCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Submit a new intelligence report.
    - **mission_id**: valid mission ID
    - **raw_text**: minimum 10 characters, max 2000
    """
    new_report = models.IntelReport(
        mission_id=intel.mission_id,
        agent_id=current_user.id,
        raw_text=intel.raw_text
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    report_data = schemas.IntelReportResponse.model_validate(new_report).model_dump()
    return success_response(
        data=report_data,
        message="Intel report submitted successfully",
        status_code=status.HTTP_201_CREATED
    )

@router.get(
    "/",
    response_model=None,
    summary="List intel reports",
    description="Retrieve intelligence reports with optional filtering by mission or agent. Supports pagination.",
    responses={
        200: {"description": "List of intel reports"},
        401: {"description": "Not authenticated"}
    }
)
def list_intel(
    mission_id: Optional[int] = Query(None, ge=1, description="Filter by mission ID"),
    agent_id: Optional[int] = Query(None, ge=1, description="Filter by agent ID"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    query = db.query(models.IntelReport)
    if mission_id:
        query = query.filter(models.IntelReport.mission_id == mission_id)
    if agent_id:
        query = query.filter(models.IntelReport.agent_id == agent_id)
    reports = query.order_by(models.IntelReport.created_at.desc()).offset(skip).limit(limit).all()
    reports_data = [schemas.IntelReportResponse.model_validate(r).model_dump() for r in reports]
    return success_response(
        data=reports_data,
        message="Intel reports retrieved successfully"
    )

@router.get(
    "/{report_id}",
    response_model=None,
    summary="Get an intel report",
    description="Retrieve a specific intelligence report by its ID.",
    responses={
        200: {"description": "Intel report details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Report not found"}
    }
)
def get_intel(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    report = db.query(models.IntelReport).filter(models.IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Intel report not found")
    return success_response(
        data=schemas.IntelReportResponse.model_validate(report).model_dump(),
        message="Intel report retrieved successfully"
    )

@router.delete(
    "/{report_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an intel report",
    description="Permanently delete an intelligence report.",
    responses={
        204: {"description": "Report deleted"},
        401: {"description": "Not authenticated"},
        404: {"description": "Report not found"}
    }
)
def delete_intel(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    report = db.query(models.IntelReport).filter(models.IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Intel report not found")
    db.delete(report)
    db.commit()
    return success_response(
        data=None,
        message="Intel report deleted successfully",
        status_code=status.HTTP_204_NO_CONTENT
    )