"""Pytest configuration and fixtures for Usefly tests."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database import Base
from src.models import SystemConfig, CrawlerRun


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@pytest.fixture
def mock_system_config(test_db: Session):
    """Create a mock system config in the test database."""
    config = SystemConfig(
        id=1,
        model_name="gpt-4o",
        api_key="test-api-key",
        use_thinking=True
    )
    test_db.add(config)
    test_db.commit()
    return config


@pytest.fixture
def mock_agent_history():
    """Create a mock Agent history object."""
    history = Mock()
    history.is_successful.return_value = True
    history.total_duration_seconds.return_value = 120.5
    history.number_of_steps.return_value = 9
    history.urls.return_value = [
        "https://example.com",
        "https://example.com/about",
        "https://example.com/contact"
    ]
    history.final_result.return_value = {
        "title": "Example Site",
        "pages_found": 3,
        "status": "success"
    }
    history.extracted_content.return_value = "Test content from website"
    history.action_history.return_value = [
        {"action": "navigate", "url": "https://example.com"}
    ]
    history.model_actions.return_value = [
        {"action_type": "click", "target": "button"}
    ]
    history.model_outputs.return_value = [
        {"output": "Page loaded"}
    ]
    history.model_thoughts.return_value = [
        {"thought": "Analyzing page"}
    ]
    history.errors.return_value = []

    return history


@pytest.fixture
def mock_llm():
    """Create a mock ChatOpenAI LLM."""
    return MagicMock()


@pytest.fixture
def mock_agent():
    """Create a mock Agent."""
    agent = AsyncMock()
    return agent
