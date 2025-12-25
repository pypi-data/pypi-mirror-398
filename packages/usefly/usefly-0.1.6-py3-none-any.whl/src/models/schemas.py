"""
API request and response schemas for scenario endpoints.

These Pydantic models are used for API request validation and response serialization.
They are separate from database models to provide a clear API contract.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, field_validator


# ==================== Crawler Analysis ====================

class CrawlerAnalysisRequest(BaseModel):
    """Request payload for crawler analysis."""
    scenario_id: str  # NOW REQUIRED - must be an existing scenario
    website_url: str
    description: str = ""
    name: str  # Scenario name (for logging purposes)
    metrics: List[str] = []  # Selected metrics
    email: str = ""  # User email


class CrawlerAnalysisResponse(BaseModel):
    """Response from crawler analysis."""
    run_id: str
    scenario_id: str
    status: str
    duration: Optional[float] = None
    steps: Optional[int] = None
    error: Optional[str] = None
    crawler_summary: Optional[str] = None  # Crawler final_result
    crawler_extracted_content: str = ""  # Crawler extracted_content (always a string)
    tasks: List[Dict] = []  # Generated UserJourneyTask objects
    tasks_metadata: Optional[Dict] = None  # Task generation metadata

    @field_validator('crawler_extracted_content', mode='before')
    @classmethod
    def ensure_string(cls, v):
        """Ensure crawler_extracted_content is always a string, never a dict"""
        if isinstance(v, str):
            return v
        elif isinstance(v, (dict, list)):
            return str(v) if v else ""
        elif v is None:
            return ""
        else:
            return str(v)


# ==================== Update Scenario Tasks ====================

class UpdateScenarioTasksRequest(BaseModel):
    """Request to update scenario task selection."""
    selected_task_numbers: List[int] = []


class UpdateScenarioTasksFullRequest(BaseModel):
    """Request to update scenario tasks array and selection (for task deletions/edits)."""
    tasks: List[Dict]
    selected_task_numbers: List[int] = []


# ==================== Generate More Tasks ====================

class GenerateMoreTasksRequest(BaseModel):
    """Request to generate additional tasks for existing scenario."""
    num_tasks: int = 15
    prompt_type: str = "friction"
    custom_prompt: Optional[str] = ""

    @field_validator('num_tasks')
    @classmethod
    def validate_num_tasks(cls, v):
        if v < 1:
            raise ValueError("num_tasks must be at least 1")
        return v

    @field_validator('prompt_type')
    @classmethod
    def validate_prompt_type(cls, v):
        if v not in ["original", "friction"]:
            raise ValueError("prompt_type must be 'original' or 'friction'")
        return v


class GenerateMoreTasksResponse(BaseModel):
    """Response from generating additional tasks."""
    scenario_id: str
    new_tasks: List[Dict]
    total_tasks: int
    tasks_metadata: Dict
    message: str


# ==================== Async Analysis ====================

class AsyncAnalysisResponse(BaseModel):
    """Response from starting async crawler analysis."""
    run_id: str
    scenario_id: str
    status: str  # "in_progress"
    message: str
