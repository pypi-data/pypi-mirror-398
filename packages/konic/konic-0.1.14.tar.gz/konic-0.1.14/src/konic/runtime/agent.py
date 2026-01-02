"""Agent registration for Konic Cloud Platform.

This module provides the agent registration mechanism used by the
Konic engine to discover and load agents for training.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from konic.common.errors.cli import KonicValidationError

if TYPE_CHECKING:
    from konic.agent import KonicAgent

_REGISTERED_AGENT_INSTANCE: KonicAgent | None = None
_REGISTERED_ENV_CLASS: Any = None


def _is_finetuning_agent(agent_instance: Any) -> bool:
    """Check if the agent is a finetuning agent.

    Finetuning agents have the get_finetuning_method method, which distinguishes
    them from standard RL agents. Finetuning agents may not have an environment
    at registration time since the environment requires the model to be loaded.

    Args:
        agent_instance: The agent instance to check.

    Returns:
        True if the agent is a finetuning agent, False otherwise.
    """
    return hasattr(agent_instance, "get_finetuning_method") and callable(
        getattr(agent_instance, "get_finetuning_method")
    )


def _perform_registration(agent_instance: KonicAgent, name: str) -> KonicAgent:
    """
    Internal function to perform agent registration.

    Args:
        agent_instance: The KonicAgent instance to register
        name: The name to register the agent under

    Returns:
        The registered agent instance

    Raises:
        KonicValidationError: If validation fails
    """
    global _REGISTERED_AGENT_INSTANCE, _REGISTERED_ENV_CLASS

    if not name:
        raise KonicValidationError("Agent name is required.")

    if inspect.isclass(agent_instance):
        raise KonicValidationError(
            f"Expected an agent instance, got class {agent_instance.__name__}. "
            "Please instantiate it first."
        )

    # For finetuning agents, the environment is optional at registration time
    # because it requires the model to be loaded first (which happens during training)
    env_class = None
    if not _is_finetuning_agent(agent_instance):
        env_class = agent_instance.get_environment()

    try:
        setattr(
            agent_instance,
            "_konic_meta",
            {"name": name, "env_module": env_class},
        )
    except AttributeError as e:
        raise KonicValidationError(f"Failed to set metadata on agent instance: {e}") from e

    _REGISTERED_AGENT_INSTANCE = agent_instance
    _REGISTERED_ENV_CLASS = env_class

    return agent_instance


def register_agent(agent_instance: Any, name: str) -> Any:
    """
    Register a KonicAgent instance for use with Konic Cloud Platform.

    This function must be called in your agent's entrypoint file to make
    the agent discoverable by the Konic engine.

    Args:
        agent_instance: The KonicAgent instance to register (must be instantiated)
        name: The unique name for this agent

    Returns:
        The registered agent instance

    Raises:
        KonicValidationError: If the agent is a class instead of an instance,
            or if the name is empty

    Example:
        >>> from konic.agent import KonicAgent
        >>> from konic.runtime import register_agent
        >>>
        >>> agent = KonicAgent(environment=MyEnvironment())
        >>> register_agent(agent, name="my-trading-agent")
    """
    return _perform_registration(agent_instance, name)


def get_registered_agent() -> tuple[Any, Any]:
    """
    Get the registered agent and environment class.

    This function is used internally by the Konic engine to retrieve
    the registered agent after loading the agent module.

    Returns:
        A tuple of (agent_instance, environment_class). Both may be None
        if no agent has been registered.
    """
    return _REGISTERED_AGENT_INSTANCE, _REGISTERED_ENV_CLASS
