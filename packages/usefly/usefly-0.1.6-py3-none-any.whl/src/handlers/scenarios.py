from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Callable
import uuid
from collections import deque
from datetime import datetime
from urllib.parse import urlparse, unquote
from fastapi import BackgroundTasks

from src.models import (
    Scenario, SystemConfig, ScenarioCreate,
    CrawlerRun, TaskList
)
from src.common.browser_use_common import run_browser_use_agent_with_hooks
from src.handlers.task_generation import (
    generate_tasks,
    renumber_tasks,
    update_generation_metadata,
    calculate_auto_selected_tasks
)

# Shared tracking for scenario analysis runs (reuses persona_runner's pattern)
from src.handlers import persona_runner

MAX_LOG_ENTRIES = 50


def list_scenarios(db: Session) -> List[Scenario]:
    """List all test scenarios."""
    return db.query(Scenario).order_by(Scenario.created_at.desc()).all()

def create_scenario(db: Session, scenario: ScenarioCreate) -> Scenario:
    """Create a new test scenario."""
    db_scenario = Scenario(
        id=str(uuid.uuid4()),
        name=scenario.name,
        website_url=scenario.website_url,
        personas=scenario.personas or ["crawler"],
        description=scenario.description,
        metrics=scenario.metrics,
        email=scenario.email,
        tasks=scenario.tasks,
        selected_task_indices=scenario.selected_task_indices,
        tasks_metadata=scenario.tasks_metadata,
        discovered_urls=scenario.discovered_urls,
        crawler_final_result=scenario.crawler_final_result,
        crawler_extracted_content=scenario.crawler_extracted_content
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def get_scenario(db: Session, scenario_id: str) -> Optional[Scenario]:
    """Get a specific test scenario."""
    return db.query(Scenario).filter(Scenario.id == scenario_id).first()

def delete_scenario(db: Session, scenario_id: str) -> bool:
    """Delete a test scenario and all related records."""
    from src.models import PersonaRun, CrawlerRun

    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        return False

    # Delete related records first to avoid foreign key constraint violations
    db.query(PersonaRun).filter(PersonaRun.config_id == scenario_id).delete()
    db.query(CrawlerRun).filter(CrawlerRun.scenario_id == scenario_id).delete()

    # Now delete the scenario
    db.delete(scenario)
    db.commit()
    return True

def decode_url(url: str) -> str:
    """Decode URL-encoded characters to original form."""
    return unquote(url)


def process_urls(urls: List[str]) -> List[Dict[str, str]]:
    """
    Process URLs to store both encoded and decoded versions.
    Removes duplicates based on encoded URL.

    Args:
        urls: List of URLs from browser-use history

    Returns:
        List of dicts with 'url' (encoded) and 'url_decoded' (decoded)
    """
    seen = set()
    result = []

    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append({
                "url": url,
                "url_decoded": decode_url(url)
            })

    return result


def init_analysis_status(
    run_id: str,
    scenario_id: str,
    scenario_name: str,
    website_url: str
):
    """Initialize analysis run status for tracking in the status bar."""
    persona_runner._active_runs[run_id] = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "report_id": None,
        "run_type": "scenario_analysis",
        "status": "in_progress",
        "total_tasks": 1,  # Analysis counts as 1 "task" with phases
        "completed_tasks": 0,
        "failed_tasks": 0,
        "agent_run_ids": [],
        "task_progress": [{
            "task_index": 0,
            "persona": "Crawler",
            "status": "running",
            "current_step": 0,
            "max_steps": 30,
            "current_action": "crawling",
            "current_url": website_url,
            "started_at": datetime.now().isoformat(),
            "error": None,
            "phase": "crawling"  # Custom field for analysis phases
        }],
        "started_at": datetime.now().isoformat(),
        "logs": deque(maxlen=MAX_LOG_ENTRIES)
    }
    _add_analysis_log(run_id, f"Starting website analysis: {website_url}")


def _add_analysis_log(run_id: str, message: str):
    """Add a log entry to the analysis run."""
    if run_id in persona_runner._active_runs:
        timestamp = datetime.now().strftime("%H:%M:%S")
        persona_runner._active_runs[run_id]["logs"].append(f"[{timestamp}] {message}")


def update_analysis_phase(
    run_id: str,
    phase: str,
    current_step: Optional[int] = None,
    current_action: Optional[str] = None,
    current_url: Optional[str] = None
):
    """Update the current phase of the analysis."""
    if run_id not in persona_runner._active_runs:
        return

    run = persona_runner._active_runs[run_id]
    if len(run["task_progress"]) > 0:
        progress = run["task_progress"][0]
        progress["phase"] = phase
        progress["current_action"] = current_action or phase

        if current_step is not None:
            progress["current_step"] = current_step
        if current_url is not None:
            progress["current_url"] = current_url

    _add_analysis_log(run_id, f"Phase: {phase}")


def complete_analysis(run_id: str, success: bool, error: Optional[str] = None):
    """Mark the analysis as completed or failed."""
    if run_id not in persona_runner._active_runs:
        return

    run = persona_runner._active_runs[run_id]

    if success:
        run["status"] = "completed"
        run["completed_tasks"] = 1
        if len(run["task_progress"]) > 0:
            run["task_progress"][0]["status"] = "completed"
            run["task_progress"][0]["phase"] = "completed"
        _add_analysis_log(run_id, "Analysis completed successfully")
    else:
        run["status"] = "failed"
        run["failed_tasks"] = 1
        if len(run["task_progress"]) > 0:
            run["task_progress"][0]["status"] = "failed"
            run["task_progress"][0]["error"] = error
        _add_analysis_log(run_id, f"Analysis failed: {error}")

    run["completed_at"] = datetime.now().isoformat()


async def analyze_website_async(db_session_factory, request, run_id: str, scenario_id: str):
    """
    Run website analysis asynchronously in background.
    Updates progress via the active runs tracker.
    """
    db = db_session_factory()
    try:
        sys_config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        if not sys_config:
            complete_analysis(run_id, False, "System configuration not found")
            return

        # Phase 1: Crawling
        update_analysis_phase(run_id, "crawling", current_action="Exploring website")

        with open('src/prompts/website_crawler_prompt.txt', 'r') as f:
            task = f.read()
            task = task.replace('{website}', request.website_url)
            task = task.replace('{description}', request.description or "")

        # Create progress callback for crawler
        def on_step_progress(step: int, action: Optional[str], url: Optional[str]):
            update_analysis_phase(
                run_id=run_id,
                phase="crawling",
                current_step=step,
                current_action=action,
                current_url=url
            )

        history = await run_browser_use_agent_with_hooks(
            task=task,
            system_config=sys_config,
            max_steps=30,
            on_step_callback=on_step_progress
        )

        raw_urls = history.urls()
        processed_urls = process_urls(raw_urls)
        final_result = history.final_result()
        extracted_content = history.extracted_content()
        duration = history.total_duration_seconds()
        steps_completed = history.number_of_steps()
        is_successful = history.is_successful()
        error_list = history.errors()
        error_str = str(error_list[0]) if error_list else None

        if not is_successful:
            complete_analysis(run_id, False, error_str or "Crawler failed")
            return

        # Phase 2: Generating tasks
        update_analysis_phase(run_id, "generating_tasks", current_action="Generating user journeys")
        _add_analysis_log(run_id, "Generating user journey tasks...")

        task_list = generate_tasks(
            crawler_result=final_result,
            existing_tasks=[],
            system_config=sys_config
        )

        task_list.website_url = request.website_url

        # Calculate persona distribution
        persona_counts = {}
        for t in task_list.tasks:
            persona_counts[t.persona] = persona_counts.get(t.persona, 0) + 1

        tasks_metadata = {
            "total_tasks": task_list.total_tasks,
            "persona_distribution": persona_counts,
            "generated_at": datetime.now().isoformat()
        }

        tasks_list = [t.dict() for t in task_list.tasks]

        # Auto-select all generated tasks
        selected_indices = list(range(len(tasks_list)))
        selected_task_numbers = [t.get("number") for t in tasks_list]

        tasks_metadata["total_selected"] = len(selected_indices)
        tasks_metadata["selected_task_numbers"] = selected_task_numbers

        # Convert extracted content to string
        extracted_content_str = ""
        if isinstance(extracted_content, str):
            extracted_content_str = extracted_content if extracted_content else ""
        elif isinstance(extracted_content, (dict, list)):
            if extracted_content:
                extracted_content_str = str(extracted_content)
        elif extracted_content is not None:
            extracted_content_str = str(extracted_content)

        # Phase 3: Update existing scenario with results
        update_analysis_phase(run_id, "saving", current_action="Updating scenario")
        _add_analysis_log(run_id, f"Updating scenario with {len(tasks_list)} tasks...")

        # Fetch existing scenario
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            complete_analysis(run_id, False, "Scenario not found")
            return

        # Update scenario with crawler results
        scenario.tasks = tasks_list
        scenario.tasks_metadata = tasks_metadata
        scenario.selected_task_indices = selected_indices
        scenario.discovered_urls = processed_urls
        scenario.crawler_final_result = str(final_result) if final_result else ""
        scenario.crawler_extracted_content = extracted_content_str

        # Create crawler run record (historical)
        crawler_run = CrawlerRun(
            id=str(uuid.uuid4()),
            scenario_id=scenario_id,
            status="success" if is_successful else "error",
            timestamp=datetime.now(),
            duration=duration,
            steps_completed=steps_completed,
            total_steps=30,
            final_result=str(final_result) if final_result else "",
            extracted_content=extracted_content_str
        )
        db.add(crawler_run)
        db.commit()

        # Mark as completed
        complete_analysis(run_id, True)
        _add_analysis_log(run_id, f"Scenario updated with {len(tasks_list)} tasks")

    except Exception as e:
        complete_analysis(run_id, False, str(e))
        print(f"Error in analyze_website_async: {e}")
    finally:
        db.close()


def start_async_analysis(db_session_factory, request, background_tasks: BackgroundTasks) -> Dict:
    """
    Start async website analysis on an EXISTING scenario.
    The scenario must already exist in the database.
    """
    db = db_session_factory()
    try:
        # Validate scenario exists
        scenario = db.query(Scenario).filter(Scenario.id == request.scenario_id).first()
        if not scenario:
            raise ValueError(f"Scenario {request.scenario_id} not found")

        run_id = str(uuid.uuid4())
        scenario_id = request.scenario_id  # Use provided scenario_id

        # Initialize tracking immediately so it shows in status bar
        init_analysis_status(run_id, scenario_id, scenario.name, request.website_url)

        # Schedule the async analysis task via FastAPI BackgroundTasks
        background_tasks.add_task(analyze_website_async, db_session_factory, request, run_id, scenario_id)

        return {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "status": "in_progress",
            "message": f"Analysis started for {request.website_url}"
        }
    finally:
        db.close()


def update_scenario_tasks(db: Session, scenario_id: str, request) -> Scenario:
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise ValueError("Scenario not found")

    all_tasks = scenario.tasks or []

    selected_indices = [
        i for i, task in enumerate(all_tasks)
        if task.get("number") in request.selected_task_numbers
    ]

    scenario.selected_task_indices = selected_indices

    current_metadata = scenario.tasks_metadata or {}
    scenario.tasks_metadata = {
        **current_metadata,
        "total_selected": len(selected_indices),
        "selected_task_numbers": request.selected_task_numbers,
    }

    db.commit()
    db.refresh(scenario)

    return scenario


def update_scenario_tasks_full(db: Session, scenario_id: str, request) -> Scenario:
    """
    Update scenario tasks array and selection.
    Used when tasks are deleted, edited, or added in the UI.
    """
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise ValueError("Scenario not found")

    # Update the tasks array
    scenario.tasks = request.tasks

    # Calculate selected indices from task numbers
    selected_indices = [
        i for i, task in enumerate(request.tasks)
        if task.get("number") in request.selected_task_numbers
    ]

    scenario.selected_task_indices = selected_indices

    # Update metadata
    current_metadata = scenario.tasks_metadata or {}

    # Recalculate persona distribution
    persona_counts = {}
    for task in request.tasks:
        persona = task.get("persona", "Unknown")
        persona_counts[persona] = persona_counts.get(persona, 0) + 1

    scenario.tasks_metadata = {
        **current_metadata,
        "total_tasks": len(request.tasks),
        "total_selected": len(selected_indices),
        "selected_task_numbers": request.selected_task_numbers,
        "persona_distribution": persona_counts,
    }

    db.commit()
    db.refresh(scenario)

    return scenario


def generate_more_tasks(db: Session, scenario_id: str, request) -> Dict:
    """
    Generate additional tasks for an existing scenario.

    This function orchestrates the task generation process by:
    1. Loading the scenario and system configuration
    2. Generating new tasks using unified task generation
    3. Renumbering and merging with existing tasks
    4. Updating metadata and auto-selecting new tasks
    """
    # Load required data from database
    scenario = _get_scenario_or_raise(db, scenario_id)
    sys_config = _get_system_config_or_raise(db)

    existing_tasks = scenario.tasks or []

    # Generate new tasks using unified task generation (always use friction prompt)
    new_task_list = generate_tasks(
        crawler_result=scenario.crawler_final_result,
        existing_tasks=existing_tasks,
        system_config=sys_config,
        num_tasks=request.num_tasks,
        custom_prompt=request.custom_prompt
    )

    # Renumber and merge tasks
    renumbered_tasks = renumber_tasks(new_task_list.tasks, existing_tasks)
    all_tasks = existing_tasks + renumbered_tasks

    # Update scenario with new tasks and metadata
    scenario.tasks = all_tasks
    scenario.tasks_metadata = update_generation_metadata(
        current_metadata=scenario.tasks_metadata or {},
        new_tasks=renumbered_tasks,
        all_tasks=all_tasks,
        custom_prompt_used=bool(request.custom_prompt)
    )

    # Auto-select new tasks
    current_selected = (scenario.tasks_metadata or {}).get("selected_task_numbers", [])
    new_task_numbers = [t["number"] for t in renumbered_tasks]
    selected_indices, all_selected = calculate_auto_selected_tasks(
        all_tasks=all_tasks,
        current_selected_numbers=current_selected,
        new_task_numbers=new_task_numbers
    )

    scenario.selected_task_indices = selected_indices
    scenario.tasks_metadata["selected_task_numbers"] = all_selected
    scenario.tasks_metadata["total_selected"] = len(all_selected)

    # Persist changes
    db.commit()
    db.refresh(scenario)

    return {
        "scenario_id": scenario.id,
        "new_tasks": renumbered_tasks,
        "total_tasks": len(all_tasks),
        "tasks_metadata": scenario.tasks_metadata,
        "message": f"Generated {len(renumbered_tasks)} new tasks using friction prompt"
    }


def _get_scenario_or_raise(db: Session, scenario_id: str) -> Scenario:
    """Helper to get scenario or raise clear error."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise ValueError("Scenario not found")
    return scenario


def _get_system_config_or_raise(db: Session) -> SystemConfig:
    """Helper to get system config or raise clear error."""
    sys_config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if not sys_config:
        raise ValueError("System configuration not found")
    return sys_config


def get_distinct_personas(db: Session) -> dict:
    """Get all unique persona types from persona_runs table."""
    from sqlalchemy import text
    
    result = db.execute(text("SELECT DISTINCT persona_type FROM persona_runs"))
    personas = [row[0] for row in result.fetchall() if row[0]]
    
    return {
        "personas": sorted(personas)
    }


