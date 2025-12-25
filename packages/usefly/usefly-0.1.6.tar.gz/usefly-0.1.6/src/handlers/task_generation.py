from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from langchain_openai import ChatOpenAI as LangchainChatOpenAI
from langchain_anthropic import ChatAnthropic
from browser_use import ChatGoogle, ChatGroq

from src.models import TaskList, SystemConfig


def _get_llm_for_task_generation(system_config: SystemConfig):
    """Initialize LLM based on provider configuration for task generation."""
    provider = system_config.provider.lower()

    if provider == "openai":
        return LangchainChatOpenAI(model=system_config.model_name, api_key=system_config.api_key)
    elif provider == "claude":
        return ChatAnthropic(model=system_config.model_name, api_key=system_config.api_key)
    elif provider == "groq":
        return ChatGroq(model=system_config.model_name, api_key=system_config.api_key)
    elif provider == "google":
        return ChatGoogle(model=system_config.model_name, api_key=system_config.api_key)
    else:
        # Default to OpenAI if provider unknown
        return LangchainChatOpenAI(model=system_config.model_name, api_key=system_config.api_key)


def load_prompt_template(num_tasks: int, custom_prompt: Optional[str] = None) -> str:
    """Load the friction task generator prompt template."""
    prompt_file = "src/prompts/task_generator_prompt.txt"

    with open(prompt_file) as f:
        task_prompt = f.read()

    # Replace placeholders
    task_prompt = task_prompt.replace("{num_tasks}", str(num_tasks))
    if "{custom_prompt}" in task_prompt:
        task_prompt = task_prompt.replace("{custom_prompt}", custom_prompt or "")

    return task_prompt


def prepare_generation_context(
    existing_tasks: List[Dict],
    crawler_result: any,
    max_context_tasks: int = 10
) -> Tuple[str, str]:
    if isinstance(crawler_result, str):
        try:
            crawler_result = json.loads(crawler_result)
        except json.JSONDecodeError:
            pass  # Keep as string if JSON parsing fails

    # Convert crawler result to string
    crawler_str = (
        json.dumps(crawler_result, indent=2)
        if isinstance(crawler_result, dict)
        else str(crawler_result)
    )

    # Build existing tasks summary
    tasks_for_context = existing_tasks[:max_context_tasks]
    existing_summary = "\n".join([
        f"Task {t.get('number')}: {t.get('goal')}"
        for t in tasks_for_context
    ])

    return existing_summary, crawler_str


def generate_tasks(
    crawler_result: any,
    existing_tasks: List[Dict],
    system_config: SystemConfig,
    num_tasks: int = 10,
    custom_prompt: Optional[str] = None
) -> TaskList:
    prompt_template = load_prompt_template(
        num_tasks=num_tasks,
        custom_prompt=custom_prompt
    )

    existing_summary, crawler_context = prepare_generation_context(
        existing_tasks=existing_tasks,
        crawler_result=crawler_result
    )

    task_list = generate_tasks_with_llm(
        prompt_template=prompt_template,
        existing_tasks_summary=existing_summary,
        crawler_context=crawler_context,
        system_config=system_config
    )

    return task_list


def generate_tasks_with_llm(
    prompt_template: str,
    existing_tasks_summary: str,
    crawler_context: str,
    system_config: SystemConfig
) -> TaskList:
    llm = _get_llm_for_task_generation(system_config)
    agent = llm.with_structured_output(TaskList)

    if existing_tasks_summary:
        input_text = (
            f"{prompt_template}\n\n"
            f"### Existing Tasks (avoid duplication):\n{existing_tasks_summary}\n\n"
            f"### Website Structure:\n{crawler_context}"
        )
    else:
        input_text = (
            f"{prompt_template}\n\n"
            f"Here's the website structure content, generate the response from it:\n"
            f"{crawler_context}"
        )

    try:
        task_list = agent.invoke(input_text)
        return task_list
    except Exception as e:
        raise ValueError(f"Task generation failed: {str(e)}")


def renumber_tasks(new_tasks: List, existing_tasks: List[Dict]) -> List[Dict]:
    max_num = max([t.get("number", 0) for t in existing_tasks]) if existing_tasks else 0

    renumbered = []
    for i, task in enumerate(new_tasks):
        task_dict = task.dict()
        task_dict["number"] = max_num + i + 1
        renumbered.append(task_dict)

    return renumbered


def calculate_persona_distribution(tasks: List[Dict]) -> Dict[str, int]:
    persona_counts = {}
    for task in tasks:
        persona = task.get("persona", "Unknown")
        persona_counts[persona] = persona_counts.get(persona, 0) + 1

    return persona_counts


def update_generation_metadata(
    current_metadata: Dict,
    new_tasks: List[Dict],
    all_tasks: List[Dict],
    custom_prompt_used: bool
) -> Dict:

    generation_history = current_metadata.get("generation_history", [])
    generation_history.append({
        "timestamp": datetime.now().isoformat(),
        "prompt_type": "friction",
        "num_generated": len(new_tasks),
        "custom_prompt_used": custom_prompt_used
    })

    persona_distribution = calculate_persona_distribution(all_tasks)

    updated_metadata = {
        **current_metadata,
        "total_tasks": len(all_tasks),
        "persona_distribution": persona_distribution,
        "generation_history": generation_history,
        "last_generated": datetime.now().isoformat()
    }

    return updated_metadata


def calculate_auto_selected_tasks(
    all_tasks: List[Dict],
    current_selected_numbers: List[int],
    new_task_numbers: List[int]
) -> Tuple[List[int], List[int]]:

    all_selected = list(set(current_selected_numbers + new_task_numbers))

    selected_indices = [
        i for i, task in enumerate(all_tasks)
        if task.get("number") in all_selected
    ]

    return selected_indices, all_selected
