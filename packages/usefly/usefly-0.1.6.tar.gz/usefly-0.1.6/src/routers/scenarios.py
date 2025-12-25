from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db, SessionLocal
from src.models import (
    ScenarioResponse,
    ScenarioCreate,
    CrawlerAnalysisRequest,
    AsyncAnalysisResponse,
    UpdateScenarioTasksRequest,
    UpdateScenarioTasksFullRequest,
    GenerateMoreTasksRequest,
    GenerateMoreTasksResponse,
    SystemConfig,
)
from src.handlers import scenarios as scenarios_handler

router = APIRouter(prefix="/api/scenario", tags=["Scenario"])


@router.get("s", response_model=List[ScenarioResponse])
def list_scenarios(db: Session = Depends(get_db)):
    """List all test scenarios."""
    return scenarios_handler.list_scenarios(db)


@router.post("s", response_model=ScenarioResponse)
def create_scenario(scenario: ScenarioCreate, db: Session = Depends(get_db)):
    """Create a new test scenario."""
    return scenarios_handler.create_scenario(db, scenario)


@router.get("s/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Get a specific test scenario."""
    scenario = scenarios_handler.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete("s/{scenario_id}")
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Delete a test scenario."""
    success = scenarios_handler.delete_scenario(db, scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"message": "Scenario deleted successfully"}


@router.post("/analyze", response_model=AsyncAnalysisResponse)
async def analyze_website(
    request: CrawlerAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start async crawler analysis on a website.
    Returns immediately with run_id and scenario_id.
    Progress can be tracked via GET /api/executions/active.
    When complete, scenario appears in /api/scenarios list.
    """
    # Validate system config exists before starting
    sys_config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if not sys_config:
        raise HTTPException(
            status_code=400,
            detail="System configuration not found. Please configure settings first at /settings"
        )

    try:
        result = scenarios_handler.start_async_analysis(SessionLocal, request, background_tasks)
        return AsyncAnalysisResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{scenario_id}/tasks")
def update_scenario_tasks(
    scenario_id: str,
    request: UpdateScenarioTasksRequest,
    db: Session = Depends(get_db)
):
    """Update selected tasks for an existing scenario."""
    try:
        return scenarios_handler.update_scenario_tasks(db, scenario_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{scenario_id}/tasks")
def update_scenario_tasks_full(
    scenario_id: str,
    request: UpdateScenarioTasksFullRequest,
    db: Session = Depends(get_db)
):
    """Update tasks array and selection for an existing scenario (for deletions/edits)."""
    try:
        return scenarios_handler.update_scenario_tasks_full(db, scenario_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{scenario_id}/generate-tasks", response_model=GenerateMoreTasksResponse)
def generate_more_tasks(
    scenario_id: str,
    request: GenerateMoreTasksRequest,
    db: Session = Depends(get_db)
):
    """Generate additional tasks for an existing scenario."""
    try:
        return scenarios_handler.generate_more_tasks(db, scenario_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personas")
def get_distinct_personas(db: Session = Depends(get_db)):
    """Get all unique persona types from persona_runs table."""
    return scenarios_handler.get_distinct_personas(db)

