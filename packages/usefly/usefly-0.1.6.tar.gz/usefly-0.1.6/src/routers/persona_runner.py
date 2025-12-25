import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db, SessionLocal
from src.models import Scenario, PersonaExecutionResponse, RunStatusResponse, ActiveExecutionsResponse
from src.handlers import persona_runner

router = APIRouter(prefix="/api", tags=["Persona Execution"])


@router.post("/persona/run/{scenario_id}", response_model=PersonaExecutionResponse)
async def run_persona(scenario_id: str, db: Session = Depends(get_db)):
    """Start running persona tasks for a scenario."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    is_valid, error_msg = persona_runner.validate_scenario_for_run(scenario)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    run_id = str(uuid.uuid4())
    report_id = str(uuid.uuid4())

    selected_indices = scenario.selected_task_indices or []
    task_count = len(selected_indices)
    await persona_runner.run_persona_tasks(
        db_session_factory=SessionLocal,
        scenario_id=scenario_id,
        report_id=report_id,
        run_id=run_id
    )

    return PersonaExecutionResponse(
        run_id=run_id,
        scenario_id=scenario_id,
        report_id=report_id,
        task_count=task_count,
        status="initiated",
        message=f"Started execution of {task_count} tasks in background"
    )


@router.get("/persona/run/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    """Get status of a specific run."""
    status = persona_runner.get_run_status(run_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail="Run not found or already completed"
        )

    return RunStatusResponse(**status)


@router.delete("/persona/run/{run_id}")
async def acknowledge_run_completion(run_id: str):
    """Acknowledge run completion and cleanup status."""
    persona_runner.cleanup_run_status(run_id)
    return {"message": "Run status cleaned up"}


@router.get("/executions/active", response_model=ActiveExecutionsResponse)
async def get_active_executions():
    """
    Get all active executions (persona runs and scenario analyses).
    Used by the status bar to restore state after page refresh.
    """
    active_runs = persona_runner.get_all_active_runs()
    return ActiveExecutionsResponse(
        executions=[RunStatusResponse(**run) for run in active_runs],
        total_count=len(active_runs)
    )
