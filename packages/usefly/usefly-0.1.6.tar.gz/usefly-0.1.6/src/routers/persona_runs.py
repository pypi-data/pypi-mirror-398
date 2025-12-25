from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models import PersonaRunResponse, PersonaRunCreate
from src.handlers import persona_runs as persona_runs_handler

router = APIRouter(prefix="/api/persona-runs", tags=["Persona Runs"])

@router.get("", response_model=List[PersonaRunResponse])
def list_persona_runs(
    config_id: str = None,
    persona_type: str = None,
    report_id: str = None,
    status: str = None,
    platform: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List persona runs with optional filters."""
    return persona_runs_handler.list_persona_runs(
        db, config_id, persona_type, report_id, status, platform, limit, offset
    )

@router.post("", response_model=PersonaRunResponse)
def create_persona_run(run: PersonaRunCreate, db: Session = Depends(get_db)):
    """Create a new persona run."""
    try:
        return persona_runs_handler.create_persona_run(db, run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{run_id}", response_model=PersonaRunResponse)
def get_persona_run(run_id: str, db: Session = Depends(get_db)):
    """Get a specific persona run."""
    run = persona_runs_handler.get_persona_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Persona run not found")
    return run
