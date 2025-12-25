"""
Scenario models for test configuration and execution.
"""

from datetime import datetime
from typing import List
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from src.database import Base


class Scenario(Base):
    """Test scenario configuration for agent runs."""
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    website_url = Column(String, nullable=False)
    personas = Column(JSON, default=[])  # List of persona types
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    description = Column(String, default="")

    # Crawler results fields
    discovered_urls = Column(JSON, default=[])  # List of {url, url_decoded} objects
    crawler_final_result = Column(String, default="")  # String from crawler
    crawler_extracted_content = Column(String, default="")  # String from crawler

    # Scenario metadata fields
    metrics = Column(JSON, default=[])  # List of selected metric strings
    email = Column(String, default="")  # Email for notifications
    tasks = Column(JSON, default=[])  # List of generated UserJourneyTask dicts
    tasks_metadata = Column(JSON, default={})  # Metadata about task generation (total_tasks, persona_distribution, etc.)
    selected_task_indices = Column(JSON, default=[])  # List of selected task indices


class ScenarioCreate(BaseModel):
    """Schema for creating a new scenario."""
    name: str  # Required - frontend must generate if empty
    website_url: str
    personas: List[str] = []
    description: str = ""
    metrics: List[str] = []
    email: str = ""
    tasks: List[dict] = []
    selected_task_indices: List[int] = []
    tasks_metadata: dict = {}
    discovered_urls: List[dict] = []
    crawler_final_result: str = ""
    crawler_extracted_content: str = ""


class ScenarioResponse(BaseModel):
    """Schema for returning scenario data."""
    id: str
    name: str
    website_url: str
    personas: List[str]
    created_at: datetime
    updated_at: datetime
    description: str = ""
    discovered_urls: List[dict] = []
    crawler_final_result: str = ""
    crawler_extracted_content: str = ""
    metrics: List[str] = []
    email: str = ""
    tasks: List[dict] = []
    tasks_metadata: dict = {}
    selected_task_indices: List[int] = []

    class Config:
        from_attributes = True
