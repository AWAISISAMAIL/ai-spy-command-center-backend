from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth_service.auth import get_current_user
from auth_service.models import User as AuthUser
from intel_service.database import SessionLocal as IntelSessionLocal
from intel_service import models as IntelModels
from mission_service.database import SessionLocal as MissionSessionLocal
from mission_service import models as MissionModels
from shared.utils import success_response, error_response
from .router import route_model, estimate_cost

router = APIRouter(prefix="/ai-brain", tags=["AI Brain"])

def get_intel_db():
    db = IntelSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mission_db():
    db = MissionSessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/summarize/{report_id}",
    response_model=None,
    summary="Summarize an intel report using AI",
    description="Fetches the specified intel report, builds a dynamic prompt including the agent's recent missions (Context API), selects the best model via the Multi-Model LLM Router (cost-optimized), and stores the generated summary. Currently uses free mock model.",
    responses={
        200: {"description": "Summary generated successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Intel report not found"}
    }
)
def summarize_intel(
    report_id: int,
    current_user: AuthUser = Depends(get_current_user),
    intel_db: Session = Depends(get_intel_db),
    mission_db: Session = Depends(get_mission_db)
):
    """
    Generate an AI-powered summary for a given intel report.
    - **report_id**: ID of the submitted intel report
    - Uses Prompt Engineering and Context Injection (recent missions)
    - Returns summary, model used, cost, and fallback status
    """
    # 1. Intel report fetch
    report = intel_db.query(IntelModels.IntelReport).filter(IntelModels.IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Intel report not found")

    # 2. Context: agent's recent missions
    recent_missions = mission_db.query(MissionModels.Mission).filter(
        MissionModels.Mission.assigned_agent_id == report.agent_id
    ).order_by(MissionModels.Mission.created_at.desc()).limit(3).all()

    mission_context = ""
    if recent_missions:
        mission_titles = [f"- {m.title} (status: {m.status})" for m in recent_missions]
        mission_context = "Agent's recent missions:\n" + "\n".join(mission_titles)
    else:
        mission_context = "No recent missions on record."

    prompt = f"""You are an intelligence analyst. Summarize the following field report in 3 key bullet points. Be concise.

{mission_context}

Field Report:
{report.raw_text}

Summary:"""

    # 3. Route to model (budget 0 = free mock)
    task_type = "summarization"
    model_choice = route_model(task_type, max_budget=0.0)
    model_name = model_choice["model_name"]
    is_fallback = model_choice["is_fallback"]

    # 4. Mock AI call
    mock_summary = f"Mock summary for report #{report.id}:\n- Based on raw intel.\n- Agent has {len(recent_missions)} recent missions.\n- No threat detected (mock)."
    token_count = len(report.raw_text.split()) * 2
    cost = estimate_cost(model_name, token_count)

    # 5. Save to DB
    report.summary = mock_summary
    report.ai_model_used = model_name
    report.cost = cost
    intel_db.commit()

    return success_response(
        data={
            "report_id": report.id,
            "summary": mock_summary,
            "ai_model": model_name,
            "cost_usd": cost,
            "is_fallback": is_fallback,
            "prompt_used": prompt  # debug only
        },
        message="Intel summarized successfully (free tier)"
    )