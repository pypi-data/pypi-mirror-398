import asyncio
import os
from pathlib import Path
from typing import Optional, Callable
from browser_use import Agent, ChatGoogle, ChatOpenAI, ChatGroq
from langchain_anthropic import ChatAnthropic
from src.models import SystemConfig, UserJourneyTask


def _get_llm(system_config: SystemConfig):
    """Initialize LLM based on provider configuration."""
    provider = system_config.provider.lower()

    if provider == "openai":
        return ChatOpenAI(model=system_config.model_name, api_key=system_config.api_key)
    elif provider == "claude":
        return ChatAnthropic(model=system_config.model_name, api_key=system_config.api_key)
    elif provider == "groq":
        return ChatGroq(model=system_config.model_name, api_key=system_config.api_key)
    elif provider == "google":
        return ChatGoogle(model=system_config.model_name, api_key=system_config.api_key)
    else:
        # Default to OpenAI if provider unknown
        return ChatOpenAI(model=system_config.model_name, api_key=system_config.api_key)


async def run_browser_use_agent(task: str, system_config: SystemConfig, max_steps: int | None = None):
    """Run browser-use agent without progress tracking (for crawler analysis)."""
    try:
        steps = max_steps or system_config.max_steps
        llm = _get_llm(system_config)

        agent = Agent(
            task=task,
            llm=llm,
            max_steps=steps,
            use_vision=True,
            use_thinking=True,
            headless=True,
            llm_timeout=90
        )

        return await agent.run()

    except Exception as e:
        raise e


async def run_browser_use_agent_with_hooks(
    task: str,
    system_config: SystemConfig,
    max_steps: int | None = None,
    on_step_callback: Optional[Callable[[int, Optional[str], Optional[str]], None]] = None
):
    """
    Run browser-use agent with lifecycle hooks for progress tracking.

    Args:
        task: The task description for the agent
        system_config: System configuration with LLM settings
        max_steps: Maximum steps for the agent to take
        on_step_callback: Callback function(step: int, action: str|None, url: str|None)
                          Called after each step with progress info
    """
    try:
        steps = max_steps or system_config.max_steps
        llm = _get_llm(system_config)

        agent = Agent(
            task=task,
            llm=llm,
            max_steps=steps,
            use_vision=True,
            use_thinking=True,
            headless=True,
            llm_timeout=90
        )

        # Define lifecycle hooks
        async def on_step_end(agent_instance):
            """Called after each agent step to report progress."""
            if on_step_callback:
                try:
                    # Get current step count
                    step_count = agent_instance.history.number_of_steps() if agent_instance.history else 0

                    # Get the last action if available
                    action = None
                    if agent_instance.history and agent_instance.history.model_actions():
                        last_action = agent_instance.history.model_actions()[-1]
                        if last_action:
                            action_keys = [k for k in last_action.keys() if k != 'interacted_element']
                            if action_keys:
                                action = action_keys[0]

                    # Get current URL
                    url = None
                    if agent_instance.state and hasattr(agent_instance.state, 'url'):
                        url = agent_instance.state.url

                    on_step_callback(step_count, action, url)
                except Exception as e:
                    # Don't let callback errors break the agent
                    print(f"Step callback error: {e}")

        return await agent.run(on_step_end=on_step_end, max_steps=steps)

    except Exception as e:
        raise e
