from pathlib import Path
import uuid
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Optional, List, Callable
from browser_use import AgentHistoryList
from sqlalchemy.orm import Session
from src.common.browser_use_common import run_browser_use_agent_with_hooks
from src.models import Scenario, SystemConfig, UserJourneyTask, PersonaRunCreate
from src.handlers.persona_runs import create_persona_run

# Enhanced structure for tracking active runs with per-task progress
_active_runs: Dict[str, Dict] = {}

# Thread pool for parallel browser task execution
# Will be initialized with max_workers from SystemConfig
_browser_executor: Optional[ThreadPoolExecutor] = None

# Maximum log entries to keep per run
MAX_LOG_ENTRIES = 50


def init_run_status(
    run_id: str,
    scenario_id: str,
    scenario_name: str,
    report_id: str,
    task_count: int,
    tasks: List[Dict],
    run_type: str = "persona_run"
):
    """Initialize run status with per-task progress tracking."""
    task_progress = []
    for idx, task in enumerate(tasks):
        task_progress.append({
            "task_index": idx,
            "persona": task.get("persona", "unknown"),
            "status": "pending",
            "current_step": 0,
            "max_steps": 30,
            "current_action": None,
            "current_url": task.get("starting_url"),
            "started_at": None,
            "error": None
        })

    _active_runs[run_id] = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "report_id": report_id,
        "run_type": run_type,
        "status": "in_progress",
        "total_tasks": task_count,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "agent_run_ids": [],
        "task_progress": task_progress,
        "started_at": datetime.now().isoformat(),
        "logs": deque(maxlen=MAX_LOG_ENTRIES)
    }
    _add_log(run_id, f"Started {run_type} with {task_count} tasks")


def _add_log(run_id: str, message: str):
    """Add a log entry to the run."""
    if run_id in _active_runs:
        timestamp = datetime.now().strftime("%H:%M:%S")
        _active_runs[run_id]["logs"].append(f"[{timestamp}] {message}")


def update_task_progress(
    run_id: str,
    task_index: int,
    status: Optional[str] = None,
    current_step: Optional[int] = None,
    current_action: Optional[str] = None,
    current_url: Optional[str] = None,
    error: Optional[str] = None
):
    """Update progress for a specific task."""
    if run_id not in _active_runs:
        return

    run = _active_runs[run_id]
    if task_index >= len(run["task_progress"]):
        return

    progress = run["task_progress"][task_index]
    persona = progress["persona"]

    if status:
        progress["status"] = status
        if status == "running" and not progress["started_at"]:
            progress["started_at"] = datetime.now().isoformat()
            _add_log(run_id, f"{persona}: Started")

    if current_step is not None:
        progress["current_step"] = current_step

    if current_action:
        progress["current_action"] = current_action
        action_display = current_action.replace("_", " ").title()
        _add_log(run_id, f"{persona}: Step {progress['current_step']} - {action_display}")

    if current_url:
        progress["current_url"] = current_url

    if error:
        progress["error"] = error
        _add_log(run_id, f"{persona}: Error - {error[:50]}")


def update_run_status(run_id: str, completed: int = 0, failed: int = 0, agent_run_id: Optional[str] = None, task_index: Optional[int] = None):
    """Update overall run status and optionally mark a task complete/failed."""
    if run_id not in _active_runs:
        return

    run = _active_runs[run_id]
    run["completed_tasks"] += completed
    run["failed_tasks"] += failed

    if agent_run_id:
        run["agent_run_ids"].append(agent_run_id)

    # Update task status
    if task_index is not None and task_index < len(run["task_progress"]):
        progress = run["task_progress"][task_index]
        if completed > 0:
            progress["status"] = "completed"
            _add_log(run_id, f"{progress['persona']}: Completed")
        elif failed > 0:
            progress["status"] = "failed"
            _add_log(run_id, f"{progress['persona']}: Failed")

    total_done = run["completed_tasks"] + run["failed_tasks"]

    if total_done >= run["total_tasks"]:
        if run["failed_tasks"] == 0:
            run["status"] = "completed"
            _add_log(run_id, "All tasks completed successfully")
        elif run["failed_tasks"] == run["total_tasks"]:
            run["status"] = "failed"
            _add_log(run_id, "All tasks failed")
        else:
            run["status"] = "partial_failure"
            _add_log(run_id, f"Completed with {run['failed_tasks']} failures")
        run["completed_at"] = datetime.now().isoformat()


def get_run_status(run_id: str) -> Optional[Dict]:
    """Get status for a specific run, converting deque to list for JSON serialization."""
    run = _active_runs.get(run_id)
    if not run:
        return None

    # Convert deque to list for JSON serialization
    result = {**run}
    result["logs"] = list(run["logs"])
    return result


def get_all_active_runs() -> List[Dict]:
    """Get all active runs for the status bar."""
    active = []
    for run_id, run in _active_runs.items():
        if run["status"] == "in_progress":
            result = {**run}
            result["logs"] = list(run["logs"])
            active.append(result)
    return active


def cleanup_run_status(run_id: str):
    """Remove a run from active tracking."""
    _active_runs.pop(run_id, None)


def validate_scenario_for_run(scenario: Scenario) -> tuple:
    if not scenario.tasks:
        return False, "Scenario has no tasks"

    selected_indices = scenario.selected_task_indices or []
    if not selected_indices:
        return False, "No tasks selected for execution"

    if any(idx >= len(scenario.tasks) for idx in selected_indices):
        return False, "Invalid task index in selection"

    return True, None


def extract_agent_events(history: AgentHistoryList) -> list:
    """Extract ALL agent actions from browser history sequentially."""
    events = []

    # Use model_actions() - official browser_use API for extracting actions
    actions = history.model_actions()
    results = history.action_results()

    for step_idx, (h, action_dict) in enumerate(zip(history.history, actions), start=1):
        # Guard against empty action dicts
        if not action_dict:
            continue

        # Get action name and params
        action_keys = [k for k in action_dict.keys() if k != 'interacted_element']
        if not action_keys:
            continue

        action_name = action_keys[0]
        action_params = action_dict[action_name]

        # Base event structure
        event = {
            'step': step_idx,
            'url': h.state.url if h.state else None,
        }

        # Extract by action type
        if action_name == 'click_element':
            event.update({
                'type': 'click',
                'index': action_params.get('index'),
                'coordinate_x': action_params.get('coordinate_x'),
                'coordinate_y': action_params.get('coordinate_y'),
            })

        elif action_name == 'scroll':
            event.update({
                'type': 'scroll',
                'direction': 'down' if action_params.get('down', True) else 'up',
                'pages': action_params.get('pages', 1.0),
                'index': action_params.get('index'),
            })

        elif action_name == 'navigate':
            event.update({
                'type': 'navigate',
                'target_url': action_params.get('url'),
                'new_tab': action_params.get('new_tab', False),
            })

        elif action_name == 'input':
            event.update({
                'type': 'input',
                'index': action_params.get('index'),
                'text': action_params.get('text'),
                'clear': action_params.get('clear', True),
            })

        elif action_name == 'search':
            event.update({
                'type': 'search',
                'query': action_params.get('query'),
                'engine': action_params.get('engine', 'google'),
            })

        elif action_name == 'go_back':
            event.update({'type': 'go_back'})

        elif action_name == 'wait':
            event.update({
                'type': 'wait',
                'seconds': action_params if isinstance(action_params, (int, float)) else action_params.get('seconds', 3),
            })

        elif action_name == 'upload_file':
            event.update({
                'type': 'upload_file',
                'index': action_params.get('index'),
                'path': action_params.get('path'),
            })

        elif action_name == 'switch':
            event.update({
                'type': 'switch_tab',
                'tab_id': action_params.get('tab_id'),
            })

        elif action_name == 'close':
            event.update({
                'type': 'close_tab',
                'tab_id': action_params.get('tab_id'),
            })

        elif action_name == 'extract':
            event.update({
                'type': 'extract',
                'query': action_params.get('query'),
                'extract_links': action_params.get('extract_links', False),
            })

        elif action_name == 'send_keys':
            event.update({
                'type': 'send_keys',
                'keys': action_params.get('keys'),
            })

        elif action_name == 'find_text':
            event.update({
                'type': 'find_text',
                'text': action_params if isinstance(action_params, str) else action_params.get('text'),
            })

        elif action_name == 'screenshot':
            event.update({'type': 'screenshot'})

        elif action_name == 'dropdown_options':
            event.update({
                'type': 'dropdown_options',
                'index': action_params.get('index'),
            })

        elif action_name == 'select_dropdown':
            event.update({
                'type': 'select_dropdown',
                'index': action_params.get('index'),
                'text': action_params.get('text'),
            })

        elif action_name == 'done':
            event.update({
                'type': 'done',
                'text': action_params.get('text'),
                'success': action_params.get('success', True),
            })

        else:
            # Fallback for unknown action types
            event.update({
                'type': action_name,
                'params': action_params,
            })

        # Add interacted_element if available (convert to dict for JSON serialization)
        if action_dict.get('interacted_element'):
            interacted_elem = action_dict['interacted_element']
            # Convert DOMInteractedElement to dict if it's not already
            if hasattr(interacted_elem, 'model_dump'):
                event['interacted_element'] = interacted_elem.model_dump(exclude_none=True)
            elif isinstance(interacted_elem, dict):
                event['interacted_element'] = interacted_elem
            else:
                event['interacted_element'] = str(interacted_elem)

        # Add result metadata
        if step_idx <= len(results) and results[step_idx - 1].metadata:
            event['metadata'] = results[step_idx - 1].metadata

        events.append(event)

    return events


async def execute_single_task(
    db: Session,
    scenario: Scenario,
    task: Dict,
    task_index: int,
    report_id: str,
    run_id: str,
    system_config: SystemConfig
) -> str:
    """Execute a single persona task with progress tracking."""
    # Mark task as running
    update_task_progress(run_id, task_index, status="running")

    try:
        journey_task = UserJourneyTask(**task)
        start_time = datetime.now()

        prompt_path = Path(__file__).parent.parent / "prompts" / "user_journey_task.txt"
        with open(prompt_path, "r") as f:
            prompt_template = f.read()

        task_description = prompt_template.format(
            persona=journey_task.persona,
            starting_url=journey_task.starting_url,
            goal=journey_task.goal,
            steps=journey_task.steps
        )
        max_steps = system_config.max_steps

        # Create progress callback for browser-use hooks
        def on_step_progress(step: int, action: Optional[str], url: Optional[str]):
            update_task_progress(
                run_id=run_id,
                task_index=task_index,
                current_step=step,
                current_action=action,
                current_url=url
            )

        # Update max_steps in task progress
        if run_id in _active_runs and task_index < len(_active_runs[run_id]["task_progress"]):
            _active_runs[run_id]["task_progress"][task_index]["max_steps"] = max_steps

        history: AgentHistoryList = await run_browser_use_agent_with_hooks(
            task=task_description,
            system_config=system_config,
            max_steps=max_steps,
            on_step_callback=on_step_progress
        )

        events = extract_agent_events(history)

        persona_run_data = PersonaRunCreate(
            config_id=scenario.id,
            report_id=report_id,
            persona_type=journey_task.persona,
            is_done=history.is_done(),
            timestamp=start_time,
            duration_seconds=history.total_duration_seconds(),
            platform="web",
            error_type="",
            steps_completed=history.number_of_steps(),
            total_steps=max_steps,
            final_result=history.final_result(),
            judgement_data=history.judgement(),
            task_description=task_description,
            task_goal=journey_task.goal,
            task_steps=journey_task.steps,
            task_url=journey_task.starting_url,
            events=events
        )

        persona_run = create_persona_run(db, persona_run_data)

        update_run_status(run_id, completed=1, agent_run_id=persona_run.id, task_index=task_index)

        return persona_run.id

    except Exception as e:
        # Update task with error
        update_task_progress(run_id, task_index, error=str(e))

        # Extract task fields properly from the task dict
        persona_run_data = PersonaRunCreate(
            config_id=scenario.id,
            report_id=report_id,
            persona_type=task.get("persona", "UNKNOWN"),
            is_done=False,
            timestamp=datetime.now(),
            duration_seconds=0,
            platform="web",
            error_type=str(e),
            steps_completed=0,
            total_steps=30,
            final_result=f"ERROR: {str(e)}",
            judgement_data={},
            task_description=task.get("goal", "UNKNOWN"),
            task_goal=task.get("goal"),
            task_steps=task.get("steps"),
            task_url=task.get("starting_url"),
            events=[]
        )

        persona_run = create_persona_run(db, persona_run_data)
        update_run_status(run_id, failed=1, agent_run_id=persona_run.id, task_index=task_index)
        return persona_run.id


def _run_task_in_thread(db_session_factory, scenario_id: str, task: Dict, task_index: int, report_id: str, run_id: str):
    """
    Run a single task in a thread with its own event loop and DB session.
    This allows parallel execution of browser tasks.
    """
    db = db_session_factory()
    try:
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        # Recreate SystemConfig from dict (can't pass SQLAlchemy objects across threads)
        sys_config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        if not sys_config:
            raise ValueError("System configuration not found")

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(execute_single_task(db, scenario, task, task_index, report_id, run_id, sys_config))
        finally:
            loop.close()
    except Exception as e:
        print(f"Error in browser task thread: {e}")
        update_run_status(run_id, failed=1, task_index=task_index)
    finally:
        db.close()


async def run_persona_tasks(db_session_factory, scenario_id: str, report_id: str, run_id: str):
    """
    Run persona tasks using ThreadPoolExecutor for controlled parallelism.
    max_workers is controlled by SystemConfig.max_browser_workers (default: 3).
    """
    global _browser_executor
    db = db_session_factory()

    try:
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        sys_config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        if not sys_config:
            raise ValueError("System configuration not found")

        # Initialize or recreate thread pool with current config
        max_workers = sys_config.max_browser_workers
        if _browser_executor is None or _browser_executor._max_workers != max_workers:
            if _browser_executor is not None:
                _browser_executor.shutdown(wait=False)
            _browser_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="browser_task")

        all_tasks = scenario.tasks or []
        selected_indices = scenario.selected_task_indices or list(range(len(all_tasks)))

        tasks_to_run = [
            all_tasks[idx]
            for idx in selected_indices
            if idx < len(all_tasks)
        ]

        if not tasks_to_run:
            raise ValueError("No tasks to run")

        # Initialize with full task list for per-task progress tracking
        init_run_status(
            run_id=run_id,
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            report_id=report_id,
            task_count=len(tasks_to_run),
            tasks=tasks_to_run,
            run_type="persona_run"
        )

        loop = asyncio.get_event_loop()
        futures = []
        for task_index, task in enumerate(tasks_to_run):
            future = loop.run_in_executor(
                _browser_executor,
                _run_task_in_thread,
                db_session_factory,
                scenario.id,
                task,
                task_index,
                report_id,
                run_id
            )
            futures.append(future)

        asyncio.create_task(_wait_for_completion(futures, run_id))

    except Exception as e:
        print(f"Fatal error in run_scenario_tasks: {e}")
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "failed"
            _active_runs[run_id]["error"] = str(e)
            _add_log(run_id, f"Fatal error: {str(e)}")
    finally:
        db.close()


async def _wait_for_completion(futures, run_id: str):
    """Wait for all futures to complete and update final status."""
    try:
        await asyncio.wait_for(
            asyncio.gather(*futures, return_exceptions=True),
            timeout=600  # 10 minutes
        )
    except asyncio.TimeoutError:
        print(f"Timeout (10 min) for run: {run_id}")
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "failed"
            _active_runs[run_id]["error"] = "Timeout: 10 minutes exceeded"
    except Exception as e:
        print(f"Error waiting for tasks: {e}")
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "failed"
            _active_runs[run_id]["error"] = str(e)

