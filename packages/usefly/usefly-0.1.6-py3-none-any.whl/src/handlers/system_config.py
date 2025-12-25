from sqlalchemy.orm import Session
from typing import Optional

from src.models import SystemConfig, SystemConfigCreate

def get_system_config(db: Session) -> Optional[SystemConfig]:
    """Get system configuration (singleton)."""
    return db.query(SystemConfig).filter(SystemConfig.id == 1).first()

def update_system_config(db: Session, config_data: SystemConfigCreate) -> SystemConfig:
    """Create or update system configuration."""
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()

    if config:
        config.model_name = config_data.model_name
        config.api_key = config_data.api_key
        config.use_thinking = config_data.use_thinking
        config.provider = config_data.provider
        config.max_steps = config_data.max_steps
        config.max_browser_workers = config_data.max_browser_workers
    else:
        config = SystemConfig(**config_data.dict())
        db.add(config)

    db.commit()
    db.refresh(config)
    return config
