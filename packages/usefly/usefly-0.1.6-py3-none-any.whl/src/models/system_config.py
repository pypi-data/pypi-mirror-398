"""
System configuration models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel
from src.database import Base


class SystemConfig(Base):
    """System configuration (singleton)."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, default=1)
    provider = Column(String, nullable=False, default="openai")
    model_name = Column(String, nullable=False, default="gpt-4o")
    api_key = Column(String, nullable=False)
    use_thinking = Column(Boolean, nullable=False, default=True)
    max_steps = Column(Integer, nullable=False, default=30)
    max_browser_workers = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemConfigCreate(BaseModel):
    """Schema for creating/updating system config."""
    provider: str = "openai"
    model_name: str = "gpt-4o"
    api_key: str
    use_thinking: bool = True
    max_steps: int = 30
    max_browser_workers: int = 3


class SystemConfigResponse(BaseModel):
    """Schema for returning system config data."""
    id: int
    provider: str
    model_name: str
    api_key: str
    use_thinking: bool
    max_steps: int
    max_browser_workers: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
