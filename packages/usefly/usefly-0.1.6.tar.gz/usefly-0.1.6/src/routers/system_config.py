from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import SystemConfigResponse, SystemConfigCreate
from src.handlers import system_config as system_config_handler

router = APIRouter(prefix="/api/system-config", tags=["System Config"])

@router.get("", response_model=SystemConfigResponse)
def get_system_config(db: Session = Depends(get_db)):
    """Get system configuration (singleton)."""
    config = system_config_handler.get_system_config(db)
    if not config:
        raise HTTPException(status_code=404, detail="System config not found")
    return config

@router.put("", response_model=SystemConfigResponse)
def update_system_config(config_data: SystemConfigCreate, db: Session = Depends(get_db)):
    """Create or update system configuration."""
    return system_config_handler.update_system_config(db, config_data)


@router.get("/status")
def get_system_config_status(db: Session = Depends(get_db)):
    """Check if system configuration is properly set up."""
    config = system_config_handler.get_system_config(db)

    if not config:
        return {"configured": False, "missing_fields": ["api_key"]}

    missing = []
    if not config.api_key or not config.api_key.strip():
        missing.append("api_key")

    return {"configured": len(missing) == 0, "missing_fields": missing}
