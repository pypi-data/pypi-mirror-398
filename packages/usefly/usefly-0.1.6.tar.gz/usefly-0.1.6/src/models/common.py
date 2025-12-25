"""
Common/shared models used across the application.
"""

from typing import List
from pydantic import BaseModel, Field


class FrictionPoint(BaseModel):
    step: str
    type: str
    duration: float


class MetricsData(BaseModel):
    time_to_value: dict = None
    onboarding: dict = None
    feature_adoption: dict = None


class UserJourneyTask(BaseModel):
    """Represents a single user journey task."""
    number: int = Field(description="Task number")
    starting_url: str = Field(description="Starting URL where user begins")
    goal: str = Field(description="User's goal/intention (e.g., 'Buy spicy onion jam for dinner party')")
    steps: str = Field(description="Step-by-step actions user takes")
    persona: str = Field(description="User persona category: SHOPPER, USER, RESEARCHER, LOCAL_VISITOR, SUPPORT_SEEKER, or BROWSER")
    stop: str = Field(description="Completion criteria - when to consider task done", default="")


class TaskList(BaseModel):
    """List of generated user journey tasks."""
    tasks: List[UserJourneyTask] = Field(description="List of user journey tasks")
    total_tasks: int = Field(default=0, description="Total number of tasks")
    website_url: str = Field(default="", description="Website base URL")
