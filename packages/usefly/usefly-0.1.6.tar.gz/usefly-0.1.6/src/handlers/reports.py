from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime

from src.models import PersonaRun, Scenario


def list_report_summaries(db: Session) -> List[Dict]:
    """
    List all unique report_ids with metadata.

    Returns a list of report summaries with scenario information and run counts.
    """
    # Query to get unique report_ids with aggregated metadata
    query = db.query(
        PersonaRun.report_id,
        PersonaRun.config_id,
        func.count(PersonaRun.id).label("run_count"),
        func.min(PersonaRun.timestamp).label("first_run"),
        func.max(PersonaRun.timestamp).label("last_run"),
    ).filter(
        PersonaRun.report_id.isnot(None)
    ).group_by(
        PersonaRun.report_id,
        PersonaRun.config_id
    ).all()

    # Build response with scenario names
    summaries = []
    for row in query:
        scenario = db.query(Scenario).filter(Scenario.id == row.config_id).first()
        scenario_name = scenario.name if scenario else "Unknown Scenario"

        summaries.append({
            "report_id": row.report_id,
            "scenario_id": row.config_id,
            "scenario_name": scenario_name,
            "run_count": row.run_count,
            "first_run": row.first_run.isoformat() if row.first_run else None,
            "last_run": row.last_run.isoformat() if row.last_run else None,
        })

    return summaries


def _query_persona_runs(
    db: Session,
    report_id: Optional[str] = None,
    config_id: Optional[str] = None,
    filters: Optional[Dict[str, str]] = None
) -> List[PersonaRun]:
    """
    Query PersonaRun records with optional filters applied at the database level.
    This is the SINGLE SOURCE OF TRUTH for filtering persona runs.
    Used by both reports and general persona run queries.
    """
    query = db.query(PersonaRun)

    # Report filter
    if report_id:
        query = query.filter(PersonaRun.report_id == report_id)

    # Config/Scenario filter
    if config_id:
        query = query.filter(PersonaRun.config_id == config_id)

    if filters:
        # Persona type filter
        if filters.get("persona_type") and filters["persona_type"] != "all":
            query = query.filter(PersonaRun.persona_type == filters["persona_type"])

        # Status filter - SINGLE SOURCE OF TRUTH
        if filters.get("status") and filters["status"] != "all":
            status = filters["status"]

            # Logic matches frontend definition of status:
            # - success: is_done=True AND judgement_data.verdict=True
            # - failed (Goal Not Met): is_done=True AND judgement_data.verdict != True
            # - error: is_done=False (crashed/timeout)

            if status == "success":
                query = query.filter(
                    PersonaRun.is_done == True,
                    func.json_extract(PersonaRun.judgement_data, '$.verdict') == True
                )
            elif status == "failed":
                # Goal Not Met: is_done but verdict is not true
                query = query.filter(
                    PersonaRun.is_done == True,
                    func.json_extract(PersonaRun.judgement_data, '$.verdict') != True
                )
            elif status == "error":
                query = query.filter(PersonaRun.is_done == False)

        # Platform filter
        if filters.get("platform") and filters["platform"] != "all":
            query = query.filter(PersonaRun.platform == filters["platform"])

    return query.all()


def get_report_aggregate(
    db: Session,
    report_id: str = None,
    config_id: str = None,
    sankey_mode: str = "compact",
    filters: Optional[Dict[str, str]] = None
) -> Optional[Dict]:
    """
    Get aggregated data for a specific report_id or scenario with optional filtering.

    Returns metrics summary and journey Sankey diagram data.
    """
    # Get all runs for this report_id and/or config_id with filters applied
    runs = _query_persona_runs(db, report_id=report_id, config_id=config_id, filters=filters)

    if not runs:
        # If filtered runs is empty but report exists (unfiltered check), return empty structure
        # This handles the case where filters match nothing but the report is valid
        if not _query_persona_runs(db, report_id=report_id):
             return None
             
        # Get scenario info from unfiltered 
        first_run = db.query(PersonaRun).filter(PersonaRun.report_id == report_id).first()
        scenario = db.query(Scenario).filter(Scenario.id == first_run.config_id).first() if first_run else None
        scenario_name = scenario.name if scenario else "Unknown Scenario"
        scenario_id = scenario.id if scenario else "unknown"

        return {
            "report_id": report_id,
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "run_count": 0,
            "metrics_summary": {
                "total_runs": 0,
                "completed_runs": 0,
                "failed_runs": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "avg_steps": 0.0,
            },
            "journey_sankey": {"nodes": [], "links": []},
        }

    # Get scenario info from first run
    scenario = db.query(Scenario).filter(Scenario.id == runs[0].config_id).first()
    scenario_name = scenario.name if scenario else "Unknown Scenario"

    # Calculate metrics summary
    metrics_summary = _calculate_metrics_summary(db, report_id, config_id, filters)

    # Get friction hotspots for Sankey diagram annotation
    friction_hotspots = get_friction_hotspots(db, report_id=report_id, config_id=config_id)

    # Generate Sankey diagram data with friction metadata
    journey_sankey = _generate_sankey_data(runs, mode=sankey_mode, friction_data=friction_hotspots)

    return {
        "report_id": report_id,
        "scenario_id": runs[0].config_id,
        "scenario_name": scenario_name,
        "run_count": len(runs),
        "metrics_summary": metrics_summary,
        "journey_sankey": journey_sankey,
    }



def _calculate_metrics_summary(
    db: Session,
    report_id: str = None,
    config_id: str = None,
    filters: Optional[Dict[str, str]] = None
) -> dict:
    """Calculate aggregated metrics using _query_persona_runs (single source of truth)."""
    base_filters = filters.copy() if filters else {}

    # Query each status type separately using _query_persona_runs
    # This ensures we use the single source of truth for status logic
    success_runs = _query_persona_runs(db, report_id=report_id, config_id=config_id, filters={**base_filters, "status": "success"})
    failed_runs = _query_persona_runs(db, report_id=report_id, config_id=config_id, filters={**base_filters, "status": "failed"})
    error_runs = _query_persona_runs(db, report_id=report_id, config_id=config_id, filters={**base_filters, "status": "error"})

    success_count = len(success_runs)
    failed_count = len(failed_runs)
    error_count = len(error_runs)
    total_count = success_count + failed_count + error_count

    return {
        "total_runs": total_count,
        "sucessfull_runs": success_count,
        "failed_runs": failed_count,
        "error_runs": error_count,
        "success_rate": success_count / total_count if total_count > 0 else 0,
        "avg_duration_seconds": 0.0,
        "avg_steps": 0.0,
    }


def extract_url_sequence_from_events(events: List[dict]) -> List[str]:
    urls = []
    for event in events:
        url = event.get('url')
        if url:
            normalized_url = url.rstrip('/')
            urls.append(normalized_url)
    return urls


def break_sequence_on_cycles(url_sequence: List[str]) -> List[List[str]]:
    if not url_sequence:
        return []

    sequences = []
    current_sequence = []
    seen_in_current = set()

    for url in url_sequence:
        if not current_sequence:
            current_sequence.append(url)
            seen_in_current.add(url)
        elif url == current_sequence[-1]:
            current_sequence.append(url)
        elif url in seen_in_current:
            sequences.append(current_sequence)
            current_sequence = [url]
            seen_in_current = {url}
        else:
            current_sequence.append(url)
            seen_in_current.add(url)

    if current_sequence:
        sequences.append(current_sequence)

    return sequences


def extract_sequences_from_runs(agent_runs: List[PersonaRun]) -> List[List[str]]:
    all_sequences = []
    for run in agent_runs:
        if not run.events:
            continue
        url_sequence = extract_url_sequence_from_events(run.events)
        broken_sequences = break_sequence_on_cycles(url_sequence)
        all_sequences.extend(broken_sequences)
    return all_sequences


def aggregate_transitions(sequences: List[List[str]]) -> Dict[tuple, int]:
    transitions = {}
    for sequence in sequences:
        for i in range(len(sequence) - 1):
            source = sequence[i]
            target = sequence[i + 1]
            if source != target:
                key = (source, target)
                transitions[key] = transitions.get(key, 0) + 1
    return transitions


def calculate_node_metrics(sequences: List[List[str]]) -> Dict[str, Dict[str, int]]:
    metrics = {}

    for sequence in sequences:
        prev_url = None
        for url in sequence:
            if url not in metrics:
                metrics[url] = {"visits": 0, "event_count": 0}

            metrics[url]["event_count"] += 1

            if url != prev_url:
                metrics[url]["visits"] += 1

            prev_url = url

    return metrics


def build_sankey_structure(
    node_metrics: Dict[str, Dict[str, int]],
    transitions: Dict[tuple, int],
    friction_data: Optional[List[Dict]] = None
) -> dict:
    """
    Build Sankey structure with optional friction metadata per node.

    Args:
        node_metrics: URL -> {visits, event_count}
        transitions: (source_url, target_url) -> count
        friction_data: List of friction hotspots from get_friction_hotspots()
    """
    urls = sorted(node_metrics.keys())
    url_to_index = {url: idx for idx, url in enumerate(urls)}

    # Map friction data to URLs
    friction_map = {}
    if friction_data:
        for hotspot in friction_data:
            url = hotspot["location"]
            if url not in friction_map:
                friction_map[url] = {
                    "friction_count": 0,
                    "friction_reasons": [],
                    "friction_impact": 0.0,
                    "example_run_ids": []
                }
            friction_map[url]["friction_count"] += hotspot["count"]
            friction_map[url]["friction_reasons"].append({
                "reason": hotspot["reason"],
                "count": hotspot["count"]
            })
            friction_map[url]["friction_impact"] += hotspot["impact_percentage"]
            friction_map[url]["example_run_ids"].extend(hotspot["example_run_ids"][:2])

    nodes = []
    for url in urls:
        node = {
            "name": url,
            "visits": node_metrics[url]["visits"],
            "event_count": node_metrics[url]["event_count"],
        }

        # Add friction metadata if available
        if url in friction_map:
            node.update({
                "friction_count": friction_map[url]["friction_count"],
                "friction_reasons": friction_map[url]["friction_reasons"],
                "friction_impact": friction_map[url]["friction_impact"],
                "example_run_ids": list(set(friction_map[url]["example_run_ids"]))[:3]
            })

        nodes.append(node)

    links = []
    for (source, target), count in transitions.items():
        links.append({
            "source": url_to_index[source],
            "target": url_to_index[target],
            "value": count,
        })

    return {"nodes": nodes, "links": links}


def remove_back_edges(transitions: Dict[tuple, int]) -> Dict[tuple, int]:
    """
    Remove transitions that create cycles.
    Keeps highest-count edges, drops edges that would close a loop.
    """
    sorted_edges = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
    
    graph = {}
    acyclic = {}

    def creates_cycle(source, target):
        # Check if there's already a path from target back to source
        visited = set()
        stack = [target]
        while stack:
            node = stack.pop()
            if node == source:
                return True
            if node not in visited:
                visited.add(node)
                stack.extend(graph.get(node, []))
        return False

    for (source, target), count in sorted_edges:
        if not creates_cycle(source, target):
            acyclic[(source, target)] = count
            graph.setdefault(source, []).append(target)

    return acyclic


# =============================================================================
# Step-Based Sankey (Full Mode)
# =============================================================================

def extract_raw_sequences_from_runs(agent_runs: List[PersonaRun]) -> List[List[str]]:
    """Extract URL sequences without breaking on cycles (for step-based mode)."""
    all_sequences = []
    for run in agent_runs:
        if not run.events:
            continue
        url_sequence = extract_url_sequence_from_events(run.events)
        if url_sequence:
            all_sequences.append(url_sequence)
    return all_sequences


def build_step_based_sankey(sequences: List[List[str]], max_steps: int = 10) -> dict:
    """
    Build Sankey data using step-based approach.
    Each node is (step_index, url) - guarantees no cycles.
    """
    node_map = {}  # (step, url) -> node_index
    nodes = []
    links_map = {}  # (source_idx, target_idx) -> count

    for sequence in sequences:
        seq_len = min(len(sequence), max_steps)
        
        for i in range(seq_len):
            url = sequence[i]
            node_key = (i, url)
            
            # Create node if needed
            if node_key not in node_map:
                node_map[node_key] = len(nodes)
                nodes.append({
                    "name": url,
                    "step": i,
                    "visits": 0,
                    "event_count": 0,
                })
            
            node_idx = node_map[node_key]
            nodes[node_idx]["visits"] += 1
            nodes[node_idx]["event_count"] += 1
            
            # Create link from previous step
            if i > 0:
                prev_url = sequence[i - 1]
                prev_key = (i - 1, prev_url)
                if prev_key in node_map:
                    prev_idx = node_map[prev_key]
                    link_key = (prev_idx, node_idx)
                    links_map[link_key] = links_map.get(link_key, 0) + 1

    links = [
        {"source": src, "target": tgt, "value": val}
        for (src, tgt), val in links_map.items()
    ]

    return {"nodes": nodes, "links": links}


# =============================================================================
# Main Entry Point
# =============================================================================

def _generate_sankey_data(
    agent_runs: List[PersonaRun],
    mode: str = "compact",
    friction_data: Optional[List[Dict]] = None
) -> dict:
    """
    Generate Sankey diagram data with optional friction metadata.

    Args:
        agent_runs: List of persona runs to analyze
        mode: "compact" (fewer nodes, drops back-edges) or "full" (step-based, no data loss)
        friction_data: Optional friction hotspot data from get_friction_hotspots()
    """
    if not agent_runs:
        return {"nodes": [], "links": []}

    if mode == "full":
        # Step-based: wider diagram, no data loss
        # Note: Friction data less useful in step-based mode since nodes are duplicated per step
        sequences = extract_raw_sequences_from_runs(agent_runs)
        return build_step_based_sankey(sequences)

    # Compact mode (default): fewer nodes, drops cycle-causing edges
    all_sequences = extract_sequences_from_runs(agent_runs)
    transitions = aggregate_transitions(all_sequences)
    acyclic_transitions = remove_back_edges(transitions)
    node_metrics = calculate_node_metrics(all_sequences)

    return build_sankey_structure(node_metrics, acyclic_transitions, friction_data)



def get_friction_hotspots(
    db: Session,
    report_id: str = None,
    config_id: str = None
) -> List[Dict]:
    """
    Identify common failure patterns (friction hotspots).
    Groups failed runs by failure reason and location (last URL).
    Only includes "goal not met" runs (is_done=True but verdict!=True).
    Excludes error runs (is_done=False - crashed/timeout).
    """
    # Get only "failed" runs (goal not met) - excludes error runs
    # Use _query_persona_runs with status="failed" filter for consistency
    failed_runs = _query_persona_runs(db, report_id=report_id, config_id=config_id, filters={"status": "failed"})

    if not failed_runs:
        return []

    # Aggregate by (Location, Reason)
    hotspots = {}

    for run in failed_runs:
        # Determine Location (Last URL)
        last_url = "Unknown Location"
        if run.events:
            # Find last event with a URL
            for event in reversed(run.events):
                if event.get("url"):
                    last_url = event.get("url").rstrip('/')
                    break
        
        # Determine Reason
        reason = "Unknown Error"
        if run.error_type:
            reason = run.error_type
        elif run.judgement_data and run.judgement_data.get("failure_reason"):
             reason = run.judgement_data.get("failure_reason")
        
        # Create unique key
        key = (last_url, reason)
        
        if key not in hotspots:
            hotspots[key] = {"count": 0, "runs": []}
        
        hotspots[key]["count"] += 1
        hotspots[key]["runs"].append(run.id)

    # Convert to list and sort by impact (count)
    result = []
    total_failures = len(failed_runs)

    for (location, reason), data in hotspots.items():
        result.append({
            "location": location,
            "reason": reason,
            "count": data["count"],
            "impact_percentage": (data["count"] / total_failures) if total_failures > 0 else 0,
            "example_run_ids": data["runs"][:3] # Return top 3 example IDs
        })
    
    # Sort by count descending
    result.sort(key=lambda x: x["count"], reverse=True)
    
    return result

