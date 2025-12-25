from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.handlers import reports

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/list")
async def list_reports(db: Session = Depends(get_db)):
    """List all unique report_ids with metadata."""
    return reports.list_report_summaries(db)


@router.get("/aggregate")
async def get_report_aggregate(
    report_id: str = Query(None, description="Filter by report ID (None for all reports)"),
    config_id: str = Query(None, description="Filter by scenario/config ID"),
    mode: str = Query("compact", description="Sankey mode: 'compact' or 'full'"),
    persona: str = Query(None, description="Filter by persona type"),
    status: str = Query(None, description="Filter by status ('completed' or 'failed')"),
    platform: str = Query(None, description="Filter by platform"),
    db: Session = Depends(get_db)
):
    """Get aggregated data for a specific report_id or scenario."""
    filters = {}
    if persona: filters["persona_type"] = persona
    if status: filters["status"] = status
    if platform: filters["platform"] = platform

    result = reports.get_report_aggregate(db, report_id, config_id=config_id, sankey_mode=mode, filters=filters)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/{report_id}/runs")
async def get_report_runs(
    report_id: str,
    persona: str = Query(None, description="Filter by persona type"),
    status: str = Query(None, description="Filter by status ('success', 'failed', or 'error')"),
    platform: str = Query(None, description="Filter by platform"),
    db: Session = Depends(get_db)
):
    """Get filtered runs for a specific report_id."""
    filters = {}
    if persona: filters["persona_type"] = persona
    if status: filters["status"] = status
    if platform: filters["platform"] = platform

    runs = reports._query_persona_runs(db, report_id=report_id, filters=filters)
    return runs



@router.get("/friction")
async def get_report_friction(
    report_id: str = Query(None, description="Filter by report ID"),
    config_id: str = Query(None, description="Filter by scenario/config ID"),
    db: Session = Depends(get_db)
):
    """
    Get friction hotspots for a report or scenario.
    Returns common failure patterns location + reason.
    """
    return reports.get_friction_hotspots(db, report_id=report_id, config_id=config_id)

