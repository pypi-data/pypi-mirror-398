from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import uuid

from src.models import PersonaRun, Scenario, PersonaRunCreate
from src.handlers.reports import _query_persona_runs

def list_persona_runs(
    db: Session,
    config_id: Optional[str] = None,
    persona_type: Optional[str] = None,
    report_id: Optional[str] = None,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PersonaRun]:
    """
    List persona runs with optional filters.
    Uses _query_persona_runs for consistent filtering logic across the app.
    """
    # Build filters dict for _query_persona_runs
    filters = {}
    if persona_type:
        filters["persona_type"] = persona_type
    if status:
        filters["status"] = status
    if platform:
        filters["platform"] = platform

    # Use _query_persona_runs for consistent filtering (SINGLE SOURCE OF TRUTH)
    runs = _query_persona_runs(
        db,
        report_id=report_id,
        config_id=config_id,
        filters=filters if filters else None
    )

    # Sort by timestamp descending
    runs = sorted(runs, key=lambda r: r.timestamp, reverse=True)

    # Apply limit and offset
    return runs[offset:offset + limit] if limit else runs[offset:]

def create_persona_run(db: Session, run: PersonaRunCreate) -> PersonaRun:
    scenario = db.query(Scenario).filter(Scenario.id == run.config_id).first()
    if not scenario:
        raise ValueError("Scenario not found")

    db_run = PersonaRun(
        id=str(uuid.uuid4()),
        config_id=run.config_id,
        report_id=run.report_id,
        persona_type=run.persona_type,
        is_done=run.is_done,
        timestamp=run.timestamp,
        duration_seconds=run.duration_seconds,
        platform=run.platform,
        error_type=run.error_type,
        steps_completed=run.steps_completed,
        total_steps=run.total_steps,
        final_result=run.final_result,
        judgement_data=run.judgement_data,
        task_description=run.task_description,
        events=run.events,
        task_goal = run.task_goal,
        task_steps = run.task_steps,
        task_url = run.task_url
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def get_persona_run(db: Session, run_id: str) -> Optional[PersonaRun]:
    """Get a specific persona run."""
    return db.query(PersonaRun).filter(PersonaRun.id == run_id).first()
