"""Tests for website analysis endpoint."""

import pytest
from unittest.mock import patch, Mock, MagicMock
from src.models import CrawlerAnalysisRequest, Scenario, ScenarioCreate
from src.handlers.scenarios import create_scenario

@pytest.mark.asyncio
async def test_analyze_website_success(mock_system_config, mock_agent_history, test_db):
    """Test successful website analysis."""

    with patch('src.handlers.scenarios.run_browser_use_agent_with_hooks') as mock_run_agent, \
         patch('src.handlers.scenarios.generate_tasks') as mock_task_gen, \
         patch('builtins.open', MagicMock()):

        # Setup mocks
        mock_run_agent.return_value = mock_agent_history

        # Mock task generation
        mock_task = Mock()
        mock_task.persona = "user"
        mock_task.dict = lambda: {"persona": "user", "name": "Task 1", "number": 1}

        mock_task2 = Mock()
        mock_task2.persona = "admin"
        mock_task2.dict = lambda: {"persona": "admin", "name": "Task 2", "number": 2}

        mock_task_list = MagicMock()
        mock_task_list.total_tasks = 2
        mock_tasks = [mock_task, mock_task2]
        mock_task_list.tasks = mock_tasks
        mock_task_gen.return_value = mock_task_list

        # Create scenario in database first
        scenario_id = "test-scenario-id"
        scenario_create = ScenarioCreate(
            name="Test Site",
            website_url="https://example.com",
            description="Test description",
            metrics=["performance"],
            email="test@example.com"
        )
        created_scenario = create_scenario(test_db, scenario_create)
        scenario_id = created_scenario.id  # Use the created scenario's ID

        # Create request
        request = CrawlerAnalysisRequest(
            scenario_id=scenario_id,
            website_url="https://example.com",
            name="Test Site",
            description="Test description",
            metrics=["performance"],
            email="test@example.com"
        )

        # Call the endpoint handler
        # analyze_website_async requires a session factory.
        # We wrap test_db in a MagicMock to avoid issues with close() if needed,
        # or just pass a lambda. Using Mock allow us to track if it was called.
        mock_session_factory = MagicMock(return_value=test_db)

        run_id = "test-run-id"

        from src.handlers.scenarios import analyze_website_async
        await analyze_website_async(
            db_session_factory=mock_session_factory, 
            request=request,
            run_id=run_id,
            scenario_id=scenario_id
        )

        # Verify DB state
        # The function commits to DB, so we should be able to query the created scenario
        scenario = test_db.query(Scenario).filter(Scenario.id == scenario_id).first()
        assert scenario is not None
        assert scenario.website_url == "https://example.com"
        assert scenario.name == "Test Site"
        # Check that tasks were saved
        assert len(scenario.tasks) == 2
        assert scenario.tasks[0]["name"] == "Task 1"
        assert scenario.tasks[1]["name"] == "Task 2"
        
        # Check metadata
        assert scenario.tasks_metadata["total_tasks"] == 2
        assert "user" in scenario.tasks_metadata["persona_distribution"]
        
        # Verify mocks were called
        mock_run_agent.assert_called_once()
        mock_task_gen.assert_called_once()
